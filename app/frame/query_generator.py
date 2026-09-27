from datetime import date, timedelta
from typing import List, Dict, Any
from app.frame.config import SAMPLE_ROUTES, BOOKING_HORIZONS

def generate_queries(collection_date: date) -> List[Dict[str, Any]]:
    """
    Generates query specifications for a given collection date based on the sampling frame.
    
    A query is defined by: Route (Origin-Destination) + Departure Date.
    Departure Date = collection_date + horizon
    """
    queries = []
    
    for route in SAMPLE_ROUTES:
        for horizon in BOOKING_HORIZONS:
            departure_date = collection_date + timedelta(days=horizon)
            
            query = {
                "route_id": route.route_id,
                "origin": route.origin,
                "destination": route.destination,
                "collection_date": collection_date,
                "horizon": horizon,
                "departure_date": departure_date,
            }
            queries.append(query)
            
    return queries
