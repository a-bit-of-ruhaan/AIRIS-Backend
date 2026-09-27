from typing import Dict, Any, Optional
from datetime import datetime

class ValidationResult:
    def __init__(self, is_valid: bool, reason: Optional[str] = None):
        self.is_valid = is_valid
        self.reason = reason

def validate_quote(quote: Dict[str, Any], query: Dict[str, Any]) -> ValidationResult:
    """
    Validates a raw quote dictionary against plausible ranges and requirements.
    Validation rules:
    - plausible range: ₹500 to ₹400,000
    - reject zero/negative fares
    - reject wrong departure date
    - reject unknown carriers
    - reject malformed required fields
    """
    try:
        price = float(quote.get("total_fare", -1))
    except (ValueError, TypeError):
        return ValidationResult(False, "Malformed total_fare")

    if price <= 0:
        return ValidationResult(False, "Zero or negative fare")
        
    if not (500 <= price <= 400000):
        return ValidationResult(False, "Fare outside plausible range (500 - 400000)")
        
    if not quote.get("carrier"):
        return ValidationResult(False, "Missing carrier")
        
    if not quote.get("cabin"):
        return ValidationResult(False, "Missing cabin")

    dep_dt_str = quote.get("departure_datetime")
    if not dep_dt_str:
        return ValidationResult(False, "Missing departure_datetime")
        
    try:
        # Simplistic parsing for ISO format
        dep_date = datetime.fromisoformat(dep_dt_str).date()
        if dep_date != query['departure_date']:
            return ValidationResult(False, "Departure date does not match query")
    except ValueError:
        return ValidationResult(False, f"Malformed departure_datetime format: {dep_dt_str}")
        
    if quote.get("origin") != query['origin'] or quote.get("destination") != query['destination']:
         return ValidationResult(False, "Route mismatch")

    return ValidationResult(True)
