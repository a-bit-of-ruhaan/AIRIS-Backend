from typing import Dict, Any

def get_cell_key(
    route: str, 
    carrier: str, 
    cabin: str, 
    fare_product_identity: str, 
    booking_horizon: int, 
    source_id: str
) -> str:
    """
    A cell is exactly:
    route × carrier × cabin × fare product identity × booking horizon × source
    """
    return f"{route}|{carrier}|{cabin}|{fare_product_identity}|{booking_horizon}|{source_id}"
