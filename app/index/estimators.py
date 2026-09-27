import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import date

def calculate_jevon_index(prices_base: Dict[str, float], prices_current: Dict[str, float]) -> float:
    """
    Bilateral Jevons index between two periods for matched items.
    P(s,t) = exp(mean_i[log(p_i,t) - log(p_i,s)])
    """
    common_items = set(prices_base.keys()).intersection(set(prices_current.keys()))
    if not common_items:
        return 1.0 # Or undefined
        
    log_ratios = []
    for item in common_items:
        log_ratios.append(np.log(prices_current[item]) - np.log(prices_base[item]))
        
    return float(np.exp(np.mean(log_ratios)))

def calculate_geks_window(prices_df: pd.DataFrame, time_col: str, item_col: str, price_col: str) -> pd.DataFrame:
    """
    GEKS over a window.
    prices_df should have ['period', 'cell_id', 'price']
    Returns a dataframe of indices for the window.
    """
    periods = sorted(prices_df[time_col].unique())
    if not periods:
         return pd.DataFrame()
         
    # Pre-compute bilateral Jevons for all pairs in the window
    # To optimize, we can construct a matrix
    p_matrix = {}
    for t in periods:
        t_data = prices_df[prices_df[time_col] == t].set_index(item_col)[price_col].to_dict()
        p_matrix[t] = t_data
        
    n_periods = len(periods)
    geks_indices = {}
    
    base_t = periods[0] # we anchor to the first period in the window for relative levels
    
    for t in periods:
        prod_P = 1.0
        for k in periods:
            # P(base, k) * P(k, t)
            p_base_k = calculate_jevon_index(p_matrix[base_t], p_matrix[k])
            p_k_t = calculate_jevon_index(p_matrix[k], p_matrix[t])
            prod_P *= (p_base_k * p_k_t)
            
        geks_indices[t] = prod_P ** (1.0 / n_periods)
        
    return pd.DataFrame([{"period": k, "geks_index": v} for k, v in geks_indices.items()])

def calculate_tpd(prices_df: pd.DataFrame, time_col: str, item_col: str, price_col: str, weight_col: str = None) -> pd.DataFrame:
    """
    Time Product Dummy estimator.
    log(p_it) = alpha + sum_t(delta_t * D_t) + sum_i(gamma_i * D_i) + epsilon_it
    """
    import statsmodels.api as sm
    
    df = prices_df.copy()
    df['log_price'] = np.log(df[price_col])
    
    # Create dummies
    # Drop first period to avoid dummy variable trap (intercept alpha is base period)
    periods = sorted(df[time_col].unique())
    if len(periods) < 2:
        return pd.DataFrame([{"period": p, "tpd_index": 1.0} for p in periods])
        
    time_dummies = pd.get_dummies(df[time_col], drop_first=True, dtype=float)
    item_dummies = pd.get_dummies(df[item_col], drop_first=True, dtype=float)
    
    X = pd.concat([time_dummies, item_dummies], axis=1)
    X = sm.add_constant(X)
    y = df['log_price']
    
    if weight_col and weight_col in df.columns:
        model = sm.WLS(y, X, weights=df[weight_col])
    else:
        model = sm.OLS(y, X)
        
    results = model.fit()
    
    indices = {periods[0]: 1.0}
    for t in periods[1:]:
        # delta_t is the coefficient for the time dummy
        # tpd index = exp(delta_t)
        if t in results.params:
             indices[t] = np.exp(results.params[t])
        else:
             # Fallback if t wasn't in dummies (e.g. string formatting issues)
             col_name = str(t)
             if col_name in results.params:
                 indices[t] = np.exp(results.params[col_name])
             else:
                 indices[t] = 1.0
                 
    return pd.DataFrame([{"period": k, "tpd_index": v} for k, v in indices.items()])

def calculate_naive_mean(prices_df: pd.DataFrame, time_col: str, price_col: str) -> pd.DataFrame:
    """
    Deliberately wrong estimator for transparency.
    naive_t = naive_(t-1) * (mean(all fares in t) / mean(all fares in t-1))
    """
    means = prices_df.groupby(time_col)[price_col].mean().sort_index()
    
    indices = []
    base_val = 1.0
    prev_mean = None
    
    for t, m in means.items():
        if prev_mean is None:
            indices.append({"period": t, "naive_index": 1.0})
        else:
            base_val = base_val * (m / prev_mean)
            indices.append({"period": t, "naive_index": base_val})
        prev_mean = m
        
    return pd.DataFrame(indices)
