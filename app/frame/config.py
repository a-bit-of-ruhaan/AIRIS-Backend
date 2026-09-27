from typing import List
from pydantic import BaseModel

class RouteDef(BaseModel):
    route_id: str
    origin: str
    destination: str
    stratum: str
    inclusion_probability: float
    horvitz_thompson_weight: float

# Fixed booking horizons (in days)
BOOKING_HORIZONS: List[int] = [1, 7, 14, 21, 30, 45, 60]

# Headline horizon
HEADLINE_HORIZON: int = 21

# Illustrative 50 domestic city pairs for SIH26056
# Based on stratified systematic PPS sampling structure
SAMPLE_ROUTES: List[RouteDef] = [
    RouteDef(route_id="DEL-BOM", origin="DEL", destination="BOM", stratum="metro-to-metro", inclusion_probability=1.0, horvitz_thompson_weight=1.0),
    RouteDef(route_id="DEL-BLR", origin="DEL", destination="BLR", stratum="metro-to-metro", inclusion_probability=1.0, horvitz_thompson_weight=1.0),
    RouteDef(route_id="BOM-BLR", origin="BOM", destination="BLR", stratum="metro-to-metro", inclusion_probability=1.0, horvitz_thompson_weight=1.0),
    # ... more routes would be defined here to reach 50
    # For now, adding a few representative ones for testing
    RouteDef(route_id="DEL-PAT", origin="DEL", destination="PAT", stratum="metro-to-tier-two", inclusion_probability=0.5, horvitz_thompson_weight=2.0),
    RouteDef(route_id="IXB-CCU", origin="IXB", destination="CCU", stratum="thin-regional", inclusion_probability=0.2, horvitz_thompson_weight=5.0),
]
