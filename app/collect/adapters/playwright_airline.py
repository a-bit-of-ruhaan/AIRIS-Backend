import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError
import logging

from app.collect.adapters.base import SourceAdapter, ParserResult
from app.collect.policy import PolicyChecker

logger = logging.getLogger(__name__)

class PlaywrightAirlineAdapter(SourceAdapter):
    """
    An adapter that uses Playwright to navigate to an airline's booking page
    and intercepts the underlying XHR/Fetch JSON responses to extract raw structured data,
    avoiding fragile HTML DOM parsing.
    """
    source_id = "airline-direct-1"
    source_name = "Indian Airline Direct (Playwright Intercept)"
    is_direct = True
    parser_version = "1.0.0"
    
    # In a real scenario, this would be the actual search URL pattern
    base_url = "https://example-airline.in/search"
    robots_url = "https://example-airline.in/robots.txt"
    intercept_url_pattern = "**/api/v1/flights/search**"

    def check_policy(self) -> bool:
        # Respect robots.txt
        return PolicyChecker.is_allowed(self.robots_url)

    def collect(self, query: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Executes a headless browser session, triggers a search, and intercepts the JSON response.
        """
        # Format dates for the URL query
        dep_date_str = query['departure_date'].strftime("%Y-%m-%d")
        search_url = f"{self.base_url}?origin={query['origin']}&destination={query['destination']}&date={dep_date_str}"
        
        captured_payload = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Use a standard browser context. 
                # CRITICAL POLICY: No fingerprint spoofing or residential proxies as per requirements.
                context = browser.new_context(
                    user_agent="AIRIS-Statistical-Collector/1.0 (+https://airis.gov.in/policy)"
                )
                page = context.new_page()
                
                # Setup network interception to grab the JSON payload
                def handle_response(response):
                    nonlocal captured_payload
                    if self.intercept_url_pattern.replace("**", "") in response.url and response.status == 200:
                        try:
                            captured_payload = response.json()
                        except Exception as e:
                            logger.error(f"Failed to parse JSON from intercepted response: {e}")

                page.on("response", handle_response)
                
                # Navigate and wait for network idle or the specific response
                # We budget for failure if the airline blocks standard headless browsers.
                page.goto(search_url, wait_until="networkidle", timeout=30000)
                
                browser.close()
                
        except TimeoutError:
            return {}, "Collection timed out. Source may be degraded or blocking."
        except Exception as e:
            return {}, f"Browser collection failed: {str(e)}"
            
        if not captured_payload:
            return {}, "Intercepted pattern not found in network traffic."
            
        return captured_payload, None

    def parse(self, raw_payload: Dict[str, Any], query: Dict[str, Any]) -> ParserResult:
        """
        Extracts expected fields from the intercepted structured JSON.
        This represents the parser contract.
        """
        quotes = []
        error = None
        
        try:
            # Assume the intercepted JSON has a structure like:
            # {"flights": [{"flightNumber": "101", "fares": [{"class": "Y", "basis": "Y123", "price": 5000, ...}]}]}
            flights = raw_payload.get("flights", [])
            
            for flight in flights:
                flight_num = flight.get("flightNumber")
                dep_time = flight.get("departureTime") # e.g. 2026-09-30T08:00:00
                
                for fare in flight.get("fares", []):
                    quote = {
                        "origin": query["origin"],
                        "destination": query["destination"],
                        "carrier": flight.get("carrierCode", "UNK"),
                        "flight_num": flight_num,
                        "departure_datetime": dep_time,
                        "cabin": fare.get("cabinClass"),
                        "rbd": fare.get("rbd"),
                        "fare_basis": fare.get("basis"),
                        "base_fare": fare.get("basePrice"),
                        "taxes": fare.get("taxes"),
                        "fees": fare.get("fees"),
                        "total_fare": fare.get("totalPrice"),
                        "currency": fare.get("currency", "INR"),
                        "is_refundable": fare.get("isRefundable", False),
                        "baggage": fare.get("baggageAllowance", "15kg")
                    }
                    quotes.append(quote)
                    
        except Exception as e:
            error = f"Parser contract violated: {str(e)}"
            
        return ParserResult(
            is_valid=error is None,
            quotes=quotes,
            error=error,
            expected_yield=(1, 50), # Expect at least 1, up to 50 quotes per route/date
            parser_version=self.parser_version
        )
