import json
import uuid
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.common.models import RawQuote, Observation, Cell
from app.normalise.validation import validate_quote
from app.normalise.product_identity import resolve_product_identity
from app.normalise.cell_assignment import get_cell_key

def normalise_quotes(db: Session, run_id: str):
    """
    Processes all raw quotes for a run, validates, deduplicates, assigns cells, and flags outliers.
    """
    raw_quotes = db.query(RawQuote).filter(RawQuote.collection_run_id == run_id).all()
    
    observations_to_add = []
    
    # Track seen for intra-run deduplication
    # Duplicate rule: same source + day, carrier + flight + time + cabin + product
    seen_keys = set()
    
    for raw in raw_quotes:
        quote_data = json.loads(raw.raw_payload_ref)
        
        query_context = {
            "origin": raw.route.split('-')[0],
            "destination": raw.route.split('-')[1],
            "departure_date": raw.departure_date,
            "horizon": raw.booking_horizon,
            "route_id": raw.route
        }
        
        # 1. Validate
        val_result = validate_quote(quote_data, query_context)
        
        # 2. Product Identity
        prod_id, is_surr = resolve_product_identity(quote_data)
        
        # 3. Deduplication check
        dep_dt_str = quote_data.get("departure_datetime", "")
        dedup_key = (
            raw.source_id,
            raw.captured_at.date(),
            quote_data.get("carrier"),
            quote_data.get("flight_num"),
            dep_dt_str,
            quote_data.get("cabin"),
            prod_id
        )
        
        is_dup = dedup_key in seen_keys
        seen_keys.add(dedup_key)
        
        # 4. Cell Assignment
        cell_key = get_cell_key(
            route=raw.route,
            carrier=quote_data.get("carrier", "UNK"),
            cabin=quote_data.get("cabin", "UNK"),
            fare_product_identity=prod_id,
            booking_horizon=raw.booking_horizon,
            source_id=raw.source_id
        )
        
        # Ensure cell exists
        cell = db.query(Cell).filter(Cell.id == cell_key).first()
        if not cell:
            cell = Cell(
                id=cell_key,
                route=raw.route,
                carrier=quote_data.get("carrier", "UNK"),
                cabin=quote_data.get("cabin", "UNK"),
                fare_product_identity=prod_id,
                booking_horizon=raw.booking_horizon,
                source_id=raw.source_id,
                definition_metadata={"created_from": raw.id}
            )
            db.add(cell)
            db.commit() # Commit to make cell available
            
        # 5. Create Observation
        obs_id = str(uuid.uuid4())
        
        try:
            dep_dt = datetime.fromisoformat(dep_dt_str)
        except:
            dep_dt = datetime.combine(raw.departure_date, datetime.min.time())
            
        obs = Observation(
            id=obs_id,
            raw_quote_id=raw.id,
            source_id=raw.source_id,
            origin=quote_data.get("origin", query_context["origin"]),
            destination=quote_data.get("destination", query_context["destination"]),
            carrier=quote_data.get("carrier", "UNK"),
            flight_identifier=quote_data.get("flight_num"),
            departure_datetime=dep_dt,
            cabin=quote_data.get("cabin", "UNK"),
            fare_basis_code=quote_data.get("fare_basis"),
            rbd=quote_data.get("rbd"),
            fare_product_identity=prod_id,
            is_refundable=quote_data.get("is_refundable"),
            baggage_allowance=quote_data.get("baggage"),
            all_inclusive_price=quote_data.get("total_fare", 0.0),
            base_fare=quote_data.get("base_fare"),
            taxes=quote_data.get("taxes"),
            fees=quote_data.get("fees"),
            currency=quote_data.get("currency", "INR"),
            booking_horizon=raw.booking_horizon,
            cell_id=cell.id,
            validation_status="VALID" if val_result.is_valid else "INVALID",
            rejection_reason=val_result.reason,
            is_duplicate=is_dup,
            is_outlier=False, # Computed below
            is_surrogate=is_surr,
            cleaning_rule_version="1.0"
        )
        db.add(obs)
        observations_to_add.append(obs)
        
    db.commit()
    
    # 6. Outlier detection (Log-price MAD within Cell for this run's period)
    # MAD is calculated across validated, non-duplicate quotes
    _flag_outliers(db, run_id)

def _flag_outliers(db: Session, run_id: str):
    """
    Uses log-price MAD:
    z_i = 0.6745 * (log(p_i) - median(log(p))) / MAD(log(p))
    Flag if |z_i| > 3.5
    """
    # Fetch valid, non-dup observations from this run
    obs = db.query(Observation).join(RawQuote).filter(
        RawQuote.collection_run_id == run_id,
        Observation.validation_status == "VALID",
        Observation.is_duplicate == False
    ).all()
    
    # Group by cell_id
    cells_map = {}
    for o in obs:
        cells_map.setdefault(o.cell_id, []).append(o)
        
    for cell_id, cell_obs in cells_map.items():
        if len(cell_obs) < 3: # Not enough for MAD
            continue
            
        prices = np.array([o.all_inclusive_price for o in cell_obs])
        log_prices = np.log(prices)
        median_log_p = np.median(log_prices)
        mad = np.median(np.abs(log_prices - median_log_p))
        
        if mad == 0:
            continue
            
        z_scores = 0.6745 * (log_prices - median_log_p) / mad
        
        for idx, z in enumerate(z_scores):
            if abs(z) > 3.5:
                cell_obs[idx].is_outlier = True
                
    db.commit()
