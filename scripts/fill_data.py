import sys
import os
sys.path.append(os.path.abspath('.'))
from datetime import date, datetime, timedelta
import random
from app.common.database import SessionLocal
from app.common.models import IndexValue, Observation, CellPrice, CollectionRun

def fill_data():
    db = SessionLocal()
    try:
        if db.query(IndexValue).count() == 0:
            print("Generating mock IndexValue data...")
            today = date.today()
            for i in range(7):
                d = today - timedelta(days=6-i)
                idx = IndexValue(
                    series_id="AIRIS-NATIONAL-21D",
                    period=d,
                    aggregate_level="national",
                    index_value=125.0 + i * 0.5 + random.random(),
                    estimator="Base",
                    coverage_grade="A",
                    publication_status="live" if i == 6 else "historical"
                )
                db.add(idx)

        db.commit()
        print("Data generation complete!")
    finally:
        db.close()

if __name__ == "__main__":
    fill_data()
