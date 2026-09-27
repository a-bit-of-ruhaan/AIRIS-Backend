import hashlib
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.common.models import CollectionRun, RunStatus, RawQuote
from app.collect.adapters.base import SourceAdapter

def execute_collection_run(db: Session, adapter: SourceAdapter, queries: list[dict]):
    """
    Executes a collection run for a specific adapter and a set of queries.
    """
    run_id = str(uuid.uuid4())
    
    # Check policy
    is_allowed = adapter.check_policy()
    
    run = CollectionRun(
        id=run_id,
        source_id=adapter.source_id,
        started_at=datetime.utcnow(),
        status=RunStatus.FAILED if not is_allowed else RunStatus.SUCCESS,
        policy_checks={"robots_txt_allowed": is_allowed},
        parser_version=adapter.parser_version
    )
    db.add(run)
    db.commit()
    
    if not is_allowed:
        run.error_summary = "Blocked by policy"
        db.commit()
        return run
        
    total_yield = 0
    expected_min, expected_max = 0, 0
        
    for query in queries:
        raw_payload, error = adapter.collect(query)
        
        if error:
            continue
            
        parser_result = adapter.parse(raw_payload, query)
        
        expected_min += parser_result.expected_yield[0]
        expected_max += parser_result.expected_yield[1]
        
        if parser_result.is_valid:
            # Store raw quotes
            for quote_data in parser_result.quotes:
                raw_quote_id = str(uuid.uuid4())
                raw_hash = hashlib.sha256(json.dumps(quote_data, sort_keys=True).encode()).hexdigest()
                
                raw_quote = RawQuote(
                    id=raw_quote_id,
                    collection_run_id=run_id,
                    source_id=adapter.source_id,
                    captured_at=datetime.utcnow(),
                    request_spec_id=f"{query['route_id']}_{query['departure_date']}",
                    route=query['route_id'],
                    departure_date=query['departure_date'],
                    booking_horizon=query['horizon'],
                    raw_payload_ref=json.dumps(quote_data), # In real app, save to S3 and put URI here
                    response_hash=raw_hash,
                    parser_version=adapter.parser_version
                )
                db.add(raw_quote)
                total_yield += 1

    run.actual_yield = total_yield
    run.expected_yield_min = expected_min
    run.expected_yield_max = expected_max
    run.finished_at = datetime.utcnow()
    
    if expected_min > 0 and total_yield < expected_min:
        run.is_degraded = True
        run.status = RunStatus.DEGRADED
        
    db.commit()
    return run
