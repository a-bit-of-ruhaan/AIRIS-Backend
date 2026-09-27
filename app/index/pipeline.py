import pandas as pd
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.common.models import CellPrice, Cell, IndexValue, IndexVintage, RouteFrame
from app.index.estimators import calculate_geks_window, calculate_tpd, calculate_naive_mean
from app.index.aggregation import aggregate_indices

def calculate_index(db: Session, target_period: date, window_days: int = 13):
    """
    Calculates GEKS, TPD, and naive mean.
    Saves to index_value and index_vintage.
    """
    # Fetch window data
    start_date = pd.to_datetime(target_period) - pd.Timedelta(days=window_days)
    
    prices = db.query(CellPrice.period, CellPrice.cell_id, CellPrice.representative_price, CellPrice.matched_observation_count, Cell.route).join(Cell).filter(
        CellPrice.period >= start_date.date(),
        CellPrice.period <= target_period
    ).all()
    
    if not prices:
        return
        
    df = pd.DataFrame(prices, columns=['period', 'cell_id', 'price', 'weight', 'route'])
    
    # Calculate for National Level (Aggregation over routes)
    # 1. Route level indices
    routes = df['route'].unique()
    
    # We will compute the index per route first, then aggregate.
    # To keep it simple for the implementation, we can run GEKS per route.
    
    route_indices_geks = []
    route_indices_tpd = []
    route_indices_naive = []
    
    for r in routes:
        route_df = df[df['route'] == r].copy()
        if len(route_df['period'].unique()) < 2:
            continue
            
        geks_res = calculate_geks_window(route_df, 'period', 'cell_id', 'price')
        tpd_res = calculate_tpd(route_df, 'period', 'cell_id', 'price', 'weight')
        naive_res = calculate_naive_mean(route_df, 'period', 'price')
        
        # Get target period value
        geks_val = geks_res[geks_res['period'] == target_period]['geks_index'].values
        tpd_val = tpd_res[tpd_res['period'] == target_period]['tpd_index'].values
        naive_val = naive_res[naive_res['period'] == target_period]['naive_index'].values
        
        if len(geks_val) > 0:
            route_indices_geks.append({'route': r, 'index': float(geks_val[0])})
        if len(tpd_val) > 0:
            route_indices_tpd.append({'route': r, 'index': float(tpd_val[0])})
        if len(naive_val) > 0:
            route_indices_naive.append({'route': r, 'index': float(naive_val[0])})

    # Fetch Weights
    route_frames = db.query(RouteFrame).all()
    weights = {rf.route_id: rf.horvitz_thompson_weight for rf in route_frames}
    
    # Aggregate to National
    agg_geks = aggregate_indices(pd.DataFrame(route_indices_geks), weights, 'route', 'index') if route_indices_geks else 1.0
    agg_tpd = aggregate_indices(pd.DataFrame(route_indices_tpd), weights, 'route', 'index') if route_indices_tpd else 1.0
    agg_naive = aggregate_indices(pd.DataFrame(route_indices_naive), weights, 'route', 'index') if route_indices_naive else 1.0
    
    # Store results (example for national level)
    for est, val in [("GEKS-Jevons", agg_geks), ("TPD", agg_tpd), ("naive-mean", agg_naive)]:
        idx_val = IndexValue(
            series_id="AIRIS-NATIONAL-21D",
            period=target_period,
            aggregate_level="national",
            index_value=val,
            estimator=est,
            coverage_grade="A", # Dummy grade for now
            publication_status="provisional",
            methodology_version="1.0",
            weight_version="1.0"
        )
        db.add(idx_val)
        db.commit() # Commit to get ID
        
        vintage = IndexVintage(
            index_value_id=idx_val.id,
            original_published_value=val,
            current_value=val,
            publication_timestamp=pd.Timestamp.utcnow(),
            status="provisional",
            methodology_version="1.0"
        )
        db.add(vintage)
        
    db.commit()
