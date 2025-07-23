import logging
from src.logger_config import get_logger, log_performance
from typing import Dict, Any, Tuple

QC_TOLERANCES = {
    'percent': 0.5,   # ±0.5% for percentages
    'months': 0.1     # ±0.1 months for survival data
}

QC_KEYWORDS = [
    "NCT Number",
    "Generic name",
    "Cancer Type",
    "Line of Treatment",
    "Number of patients",
    "Objective response rate (ORR)",
    "Progression free survival (PFS)",
    "Overall survival (OS)",
    "Adverse events (AE)",
    "Grade ≥3 adverse events (AE)",
    "Treatment emergent adverse events (TEAE) led to treatment discontinuation"
]

COLOR_RULES = [
    (1.0, 'Green'),    # 100%
    (0.75, 'Orange'), # 75% - 99%
    (0.0, 'Red')      # <75%
]

def _is_float(val):
    try:
        float(val)
        return True
    except Exception:
        return False

def _compare_values(val1, val2, field):
    # NCT Number: must match pattern
    if field == "NCT Number":
        import re
        pattern = r"NCT\\d{8}"
        return bool(val1) and bool(val2) and val1 == val2 and re.match(pattern, val1)
    # Generic name: exact match (case-insensitive, strip)
    if field == "Generic name":
        return val1.strip().lower() == val2.strip().lower()
    # Cancer Type: exact match (case-insensitive)
    if field == "Cancer Type":
        return val1.strip().lower() == val2.strip().lower()
    # Line of Treatment: exact match
    if field == "Line of Treatment":
        return val1.strip().lower() == val2.strip().lower()
    # Number of patients: numeric, exact
    if field == "Number of patients":
        return _is_float(val1) and _is_float(val2) and float(val1) == float(val2)
    # Percentages: tolerance ±0.5
    if field in ["Objective response rate (ORR)", "Adverse events (AE)", "Grade ≥3 adverse events (AE)", "Treatment emergent adverse events (TEAE) led to treatment discontinuation"]:
        if _is_float(val1) and _is_float(val2):
            return abs(float(val1) - float(val2)) <= QC_TOLERANCES['percent']
        return False
    # Survival: tolerance ±0.1 or NR
    if field in ["Progression free survival (PFS)", "Overall survival (OS)"]:
        if str(val1).strip().upper() == 'NR' and str(val2).strip().upper() == 'NR':
            return True
        if _is_float(val1) and _is_float(val2):
            return abs(float(val1) - float(val2)) <= QC_TOLERANCES['months']
        return False
    return val1 == val2

def _assign_color(match_ratio: float) -> str:
    for threshold, color in COLOR_RULES:
        if match_ratio >= threshold:
            return color
    return 'Red'

class QCValidator:
    def __init__(self):
        self.logger = get_logger(__name__)

    @log_performance
    def validate(self, main_row: Dict[str, Any], qc_row: Dict[str, Any]) -> Tuple[float, str, Dict[str, bool]]:
        """
        Compare main extraction row with QC row. Return (match_ratio, color, field_results)
        """
        matches = 0
        field_results = {}
        for field in QC_KEYWORDS:
            main_val = main_row.get(field, "")
            qc_val = qc_row.get(field, "")
            result = _compare_values(main_val, qc_val, field)
            field_results[field] = result
            if result:
                matches += 1
            else:
                self.logger.debug(f"Mismatch in field '{field}': main='{main_val}' qc='{qc_val}'")
        match_ratio = matches / len(QC_KEYWORDS)
        color = _assign_color(match_ratio)
        self.logger.info(f"QC match: {matches}/{len(QC_KEYWORDS)} ({match_ratio*100:.1f}%) - {color}")
        return match_ratio, color, field_results 