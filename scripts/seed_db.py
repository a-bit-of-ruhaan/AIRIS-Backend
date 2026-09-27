import sys
import os
sys.path.append(os.path.abspath('.'))
from app.common.database import SessionLocal, Base, engine
from app.common.models import Source, RouteFrame, Weight
from app.frame.config import SAMPLE_ROUTES
from datetime import date

def seed():
    # Only seed if tables are empty
    db = SessionLocal()
    
    try:
        if db.query(Source).count() == 0:
            s1 = Source(id="synthetic-airline-direct", name="Synthetic Airline Direct", type="airline", is_direct=True, parser_contract="1.0.0")
            db.add(s1)
            
        if db.query(RouteFrame).count() == 0:
            for r in SAMPLE_ROUTES:
                rf = RouteFrame(
                    route_id=r.route_id,
                    origin=r.origin,
                    destination=r.destination,
                    stratum=r.stratum,
                    inclusion_probability=r.inclusion_probability,
                    horvitz_thompson_weight=r.horvitz_thompson_weight,
                    effective_from=date(2026, 1, 1)
                )
                db.add(rf)
                
        if db.query(Weight).count() == 0:
             for r in SAMPLE_ROUTES:
                 w = Weight(
                     route=r.route_id,
                     weight_value=r.horvitz_thompson_weight,
                     is_illustrative=True,
                     effective_from=date(2026, 1, 1),
                     source_metadata="Illustrative"
                 )
                 db.add(w)
                 
        db.commit()
        print("Database seeded.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
