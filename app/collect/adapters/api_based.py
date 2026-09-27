import requests
from typing import Dict, Any, Optional, Tuple
from app.collect.adapters.base import SourceAdapter, ParserResult
from app.config.settings import settings

class SerpApiAdapter(SourceAdapter):
    """
    Adapter for Google Flights using SerpApi.
    """
    source_id = "serpapi-google-flights"
    source_name = "Google Flights via SerpApi"
    is_direct = False
    parser_version = "1.0.0"

    base_url = "https://serpapi.com/search.json"

    def check_policy(self) -> bool:
        return True # API provider handles policy

    def collect(self, query: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        if not settings.SERPAPI_API_KEY:
            return {}, "SERPAPI_API_KEY is not configured in environment."

        dep_date_str = query['departure_date'].strftime("%Y-%m-%d")
        
        params = {
            "engine": "google_flights",
            "departure_id": query['origin'],
            "arrival_id": query['destination'],
            "outbound_date": dep_date_str,
            "currency": "INR",
            "hl": "en",
            "type": "2", # One-way
            "api_key": settings.SERPAPI_API_KEY
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json(), None
            
        except requests.RequestException as e:
            return {}, f"SerpApi request failed: {str(e)}"

    def parse(self, raw_payload: Dict[str, Any], query: Dict[str, Any]) -> ParserResult:
        quotes = []
        error = None
        
        try:
            best_flights = raw_payload.get("best_flights", [])
            other_flights = raw_payload.get("other_flights", [])
            
            all_flights = best_flights + other_flights
            
            for flight_option in all_flights:
                price = flight_option.get("price", 0)
                flights_list = flight_option.get("flights", [])
                
                if not flights_list:
                    continue
                    
                # Simplify for direct flights primarily
                first_segment = flights_list[0]
                
                quote = {
                    "origin": query["origin"],
                    "destination": query["destination"],
                    "carrier": first_segment.get("airline", "UNK"),
                    "flight_num": first_segment.get("flight_number", "UNK"),
                    "departure_datetime": first_segment.get("departure_token", ""), # Needs actual time extraction in a real app
                    "cabin": first_segment.get("travel_class", "Economy"),
                    "rbd": "Y", # Default/Unknown from basic API
                    "fare_basis": "UNK",
                    "base_fare": float(price),
                    "taxes": 0, 
                    "fees": 0,
                    "total_fare": float(price),
                    "currency": "INR",
                    "is_refundable": False,
                    "baggage": "Standard"
                }
                quotes.append(quote)
                
        except Exception as e:
            error = f"Failed to parse SerpApi response: {str(e)}"
            
        return ParserResult(
            is_valid=error is None,
            quotes=quotes,
            error=error,
            expected_yield=(1, 50),
            parser_version=self.parser_version
        )
