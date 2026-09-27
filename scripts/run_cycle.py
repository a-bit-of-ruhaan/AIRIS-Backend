import sys
import os
sys.path.append(os.path.abspath('.'))

from datetime import date, timedelta
from app.common.database import SessionLocal
from app.collect.adapters.synthetic import SyntheticAdapter
from app.collect.adapters.api_based import SerpApiAdapter
from app.collect.engine import execute_collection_run
from app.normalise.pipeline import normalise_quotes
from app.index.cell_price import calculate_cell_prices
from app.index.pipeline import calculate_index
from app.frame.config import SAMPLE_ROUTES

def run_cycle():
    db = SessionLocal()
    try:
        # Use SerpApiAdapter for real Google Flights data
        adapter = SerpApiAdapter()
        
        # Run for the last 7 days to populate history
        for i in range(7, -1, -1):
            target_period = date.today() - timedelta(days=i)
            print(f"Running cycle for {target_period}...")
            
            queries = []
            for route in SAMPLE_ROUTES:
                for horizon in [7, 14, 21]:
                    departure_date = target_period + timedelta(days=horizon)
                    queries.append({
                        "origin": route.origin,
                        "destination": route.destination,
                        "route_id": route.route_id,
                        "departure_date": departure_date,
                        "horizon": horizon
                    })
                    
            print(f"  Executing collection run for {len(queries)} queries...")
            run = execute_collection_run(db, adapter, queries)
            print(f"  Collection run completed. ID: {run.id}, Status: {run.status}")
            
            if run.status == "SUCCESS" or run.status == "DEGRADED":
                print(f"  Normalising quotes for run {run.id}...")
                normalise_quotes(db, run.id)
                
                print(f"  Calculating cell prices for {target_period}...")
                calculate_cell_prices(db, target_period)
                
                print(f"  Calculating indices for {target_period}...")
                calculate_index(db, target_period)
                print(f"  Cycle for {target_period} completed successfully!")
            else:
                print(f"  Collection run failed for {target_period}.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_cycle()