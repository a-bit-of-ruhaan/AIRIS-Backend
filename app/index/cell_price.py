import numpy as np
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.common.models import Observation, Cell, CellPrice, CollectionRun, RawQuote

def calculate_cell_prices(db: Session, target_period: date):
    """
    Calculates cell prices (geometric mean) for a specific target_period based on 
    observations captured on that day.
    Uses only: matched, validated, non-degraded quotes.
    """
    # Find successful/active runs for the target period
    valid_runs = db.query(CollectionRun).filter(
        CollectionRun.started_at >= target_period,
        CollectionRun.started_at < target_period.__class__(target_period.year, target_period.month, target_period.day + 1 if target_period.day < 28 else 1) # Simplification for time bound
    ).filter(CollectionRun.is_degraded == False).all()
    
    run_ids = [r.id for r in valid_runs]
    
    if not run_ids:
        return
        
    obs = db.query(Observation).join(RawQuote).filter(
        RawQuote.collection_run_id.in_(run_ids),
        Observation.validation_status == "VALID",
        Observation.is_duplicate == False,
        Observation.is_outlier == False
    ).all()
    
    cells_map = {}
    for o in obs:
        cells_map.setdefault(o.cell_id, []).append(o)
        
    for cell_id, cell_obs in cells_map.items():
        prices = [o.all_inclusive_price for o in cell_obs]
        
        # p_cell,t = exp((1/n) * sum_i log(p_i,t)) (Geometric Mean)
        log_prices = np.log(prices)
        geometric_mean = np.exp(np.mean(log_prices))
        
        # Compute dispersion (e.g. coefficient of variation)
        dispersion = float(np.std(prices) / np.mean(prices)) if len(prices) > 1 else 0.0
        
        cell_price = CellPrice(
            cell_id=cell_id,
            period=target_period,
            representative_price=float(geometric_mean),
            matched_observation_count=len(cell_obs),
            valid_observation_count=len(cell_obs),
            dispersion=dispersion,
            outlier_count=0, # In real app, query outliers separately
            source_id=cell_obs[0].source_id
        )
        db.add(cell_price)
        
    db.commit()
