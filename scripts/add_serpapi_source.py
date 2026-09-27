import sys
import os
sys.path.append(os.path.abspath('.'))
from app.common.database import SessionLocal
from app.common.models import Source

def add_source():
    db = SessionLocal()
    try:
        s = db.query(Source).filter(Source.id == "serpapi-google-flights").first()
        if not s:
            s2 = Source(id="serpapi-google-flights", name="Google Flights via SerpApi", type="aggregator", is_direct=False, parser_contract="1.0.0")
            db.add(s2)
            db.commit()
            print("Added serpapi-google-flights source.")
        else:
            print("Source already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    add_source()
