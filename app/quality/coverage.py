from typing import Dict

def compute_quality_grade(
    matched_observations: int,
    contributing_cells: int,
    thin_cell_share: float,
    surrogate_product_share: float,
    spliced_share: float
) -> str:
    """
    Computes the quality grade based on worst component.
    """
    grade_obs = "D"
    if matched_observations >= 500: grade_obs = "A"
    elif matched_observations >= 200: grade_obs = "B"
    elif matched_observations >= 50: grade_obs = "C"
    
    grade_cells = "D"
    if contributing_cells >= 30: grade_cells = "A"
    elif contributing_cells >= 15: grade_cells = "B"
    elif contributing_cells >= 5: grade_cells = "C"
    
    grade_thin = "D"
    if thin_cell_share <= 0.10: grade_thin = "A"
    elif thin_cell_share <= 0.25: grade_thin = "B"
    elif thin_cell_share <= 0.50: grade_thin = "C"
    
    grade_surrogate = "D"
    if surrogate_product_share <= 0.05: grade_surrogate = "A"
    elif surrogate_product_share <= 0.25: grade_surrogate = "B"
    elif surrogate_product_share <= 0.60: grade_surrogate = "C"
    
    grade_spliced = "D"
    if spliced_share <= 0.10: grade_spliced = "A"
    elif spliced_share <= 0.30: grade_spliced = "B"
    elif spliced_share <= 0.60: grade_spliced = "C"
    
    grades = [grade_obs, grade_cells, grade_thin, grade_surrogate, grade_spliced]
    
    if "D" in grades: return "D"
    if "C" in grades: return "C"
    if "B" in grades: return "B"
    return "A"
