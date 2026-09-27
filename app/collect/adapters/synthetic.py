import json
from typing import Dict, Any, Optional
from datetime import timedelta
import random

from app.collect.adapters.base import SourceAdapter, ParserResult
from app.collect.policy import PolicyChecker

class SyntheticAdapter(SourceAdapter):
    source_id = "synthetic-airline-direct"
    source_name = "Synthetic Airline Direct"
    is_direct = True
    parser_version = "1.0.0"

    def check_policy(self) -> bool:
        return PolicyChecker.is_allowed("https://synthetic-airline.local/robots.txt")

    def collect(self, query: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
        # Generate synthetic payload
        # Deterministic random based on query for reproducibility
        seed_str = f"{query['route_id']}_{query['departure_date'].isoformat()}_{query['horizon']}"
        random.seed(seed_str)
        
        base_price = 4000.0 if query['horizon'] > 14 else 6000.0
        
        # Simulate some missing data randomly
        if random.random() < 0.05:
            return {}, "Simulated collection failure"

        quotes = []
        for flight_num in range(1, random.randint(3, 6)):
            departure_datetime = query['departure_date'].strftime("%Y-%m-%dT08:00:00")
            
            # Simulate different fare classes
            for cabin, rbd, multiplier in [("Economy", "Y", 1.0), ("Economy", "M", 1.5), ("Business", "J", 3.0)]:
                price = base_price * multiplier * (0.9 + random.random() * 0.2)
                quote = {
                    "origin": query['origin'],
                    "destination": query['destination'],
                    "carrier": "SYN",
                    "flight_num": f"SYN{flight_num * 100}",
                    "departure_datetime": departure_datetime,
                    "cabin": cabin,
                    "rbd": rbd,
                    "fare_basis": f"{rbd}SYN123",
                    "base_fare": price * 0.8,
                    "taxes": price * 0.1,
                    "fees": price * 0.1,
                    "total_fare": price,
                    "currency": "INR",
                    "is_refundable": rbd == "Y",
                    "baggage": "15kg"
                }
                quotes.append(quote)
                
        return {"data": {"flights": quotes}}, None

    def parse(self, raw_payload: Dict[str, Any], query: Dict[str, Any]) -> ParserResult:
        quotes_data = raw_payload.get("data", {}).get("flights", [])
        return ParserResult(
            is_valid=True,
            quotes=quotes_data,
            expected_yield=(2, 20),
            parser_version=self.parser_version
        )
