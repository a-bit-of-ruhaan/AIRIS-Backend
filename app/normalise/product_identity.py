from typing import Dict, Any

def resolve_product_identity(quote: Dict[str, Any]) -> tuple[str, bool]:
    """
    Resolve product identity in exact order:
    1. Fare basis code.
    2. Reservation booking designator (RBD).
    3. Constructed surrogate from: cabin, refundability, baggage allowance, change-fee flag, brand label
    
    Returns (identity_string, is_surrogate)
    """
    fare_basis = quote.get("fare_basis")
    if fare_basis:
        return (fare_basis, False)
        
    rbd = quote.get("rbd")
    if rbd:
        return (f"RBD_{rbd}", False)
        
    # Construct surrogate
    cabin = quote.get("cabin", "Unknown")
    ref = "REF" if quote.get("is_refundable") else "NONREF"
    bag = quote.get("baggage", "0kg")
    
    surrogate_id = f"SURR_{cabin}_{ref}_{bag}"
    return (surrogate_id, True)
