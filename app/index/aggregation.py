import pandas as pd
from typing import Dict

def aggregate_indices(indices_df: pd.DataFrame, weights: Dict[str, float], component_col: str, index_col: str) -> float:
    """
    Young-type weighted arithmetic mean of component indices at fixed base weights:
    I_agg,t = sum_c(w_c * I_c,t) / sum_c w_c
    """
    # Normalize weights for available components
    available_components = indices_df[component_col].unique()
    relevant_weights = {c: weights.get(c, 0.0) for c in available_components}
    
    total_weight = sum(relevant_weights.values())
    if total_weight == 0:
        return 1.0 # Fallback
        
    norm_weights = {c: w / total_weight for c, w in relevant_weights.items()}
    
    agg_val = 0.0
    for idx, row in indices_df.iterrows():
        comp = row[component_col]
        val = row[index_col]
        agg_val += val * norm_weights.get(comp, 0.0)
        
    return agg_val
