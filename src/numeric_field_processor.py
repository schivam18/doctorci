"""
Post-processing module for cleaning numeric fields from LLM output.
"""

import re
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)

def clean_field_name(field_name: str) -> str:
    """Clean field names by fixing character encoding issues."""
    if not field_name:
        return field_name
    # Replace common encoding issues
    field_name = field_name.replace('â‰¥', '≥')
    field_name = field_name.replace('â€™', "'")
    field_name = field_name.replace('â€œ', '"')
    field_name = field_name.replace('â€', '"')
    return field_name

# Define field categories based on user requirements
PERCENTAGE_FIELDS = {
    "Objective response rate (ORR)",
    "Complete Response (CR)", 
    "Pathological Complete Response (pCR)",
    "Complete Metabolic Response (CMR)",
    "Disease Control Rate or DCR",
    "Clinical Benefit Rate (CBR)",
    "Duration of Response (DOR) rate",
    "Progression free survival (PFS) rate at 6 months",
    "Progression free survival (PFS) rate at 12 months", 
    "Progression free survival (PFS) rate at 18 months",
    "Progression free survival (PFS) rate at 24 months",
    "Progression free survival (PFS) rate at 48 months",
    "Overall survival (OS) rate at 6 months",
    "Overall survival (OS) rate at 12 months",
    "Overall survival (OS) rate at 18 months", 
    "Overall survival (OS) rate at 24 months",
    "Overall survival (OS) rate at 48 months"
}

NUMERIC_FIELDS = {
    "Number of patients",
    "Progression free survival (PFS)",
    "Length of measuring PFS",
    "Hazard ratio (HR) PFS",
    "Overall survival (OS)",
    "Length of measuring OS",
    "Hazard ratio (HR) OS",
    "Event-Free Survival (EFS)",
    "Hazard ratio (HR) EFS",
    "Recurrence-Free Survival (RFS)",
    "Length of measuring RFS",
    "Hazard ratio (HR) RFS",
    "Metastasis-Free Survival (MFS)",
    "Length of measuring MFS",
    "Hazard ratio (HR) MFS",
    "Time to response (TTR)",
    "Time to Progression (TTP)",
    "Time to Next Treatment (TTNT)",
    "Time to Treatment Failure (TTF)",
    "Median Duration of response or DOR"
}

# P-VALUE FIELDS - Special handling for significance classification
P_VALUE_FIELDS = {
    "p-value of PFS", 
    "p-value of OS",
    "p-value of EFS",
    "p-value of RFS",
    "p-value of MFS"
}

ADVERSE_EVENT_FIELDS = {
    "Adverse events (AE)",
    "Treatment emergent adverse events (TEAE)",
    "Treatment-related adverse events (TRAE)",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher adverse events (AE)",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment emergent adverse events (TEAE)",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-related adverse events (TRAE)",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-emergent adverse events (TEAE)",
    "Grade 4 treatment emergent adverse events",
    "Grade 5 treatment emergent adverse events",
    "Immune related adverse events (irAEs)",
    "Treatment-emergent adverse events (TEAE) led to treatment discontinuation",
    "Adverse events (AEs) leading to discontinuation",
    "Treatment-emergent adverse events (TEAE) led to death",
    "Adverse Events leading to death",
    "Serious Adverse Events (SAE)",
    "Serious treatment emergent adverse events",
    "Serious treatment related adverse events",
    "Cytokine Release Syndrome or CRS",
    "White blood cell (WBC) decreased",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Immune related adverse events (irAEs)",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cytokine Release Syndrome or CRS",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thrombocytopenia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutropenia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Leukopenia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Nausea",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Anemia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Diarrhea",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Colitis",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hyperglycemia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutrophil count decreased",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Constipation",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Dyspnea",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cough",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pyrexia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Bleeding",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pruritus",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Rash",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonia",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thyroiditis",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hypophysitis",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hepatitis",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonitis",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Alanine aminotransferase",
    "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 White blood cell (WBC) decreased"
}

# All numeric fields combined (excluding p-values which need special handling)
ALL_NUMERIC_FIELDS = PERCENTAGE_FIELDS | NUMERIC_FIELDS | ADVERSE_EVENT_FIELDS

def is_numeric_field(field_name: str) -> bool:
    """Check if a field should contain only numbers, handling encoding issues."""
    if not field_name:
        return False
    
    # Clean the field name first
    cleaned_name = clean_field_name(field_name)
    
    # Check direct match first
    if cleaned_name in ALL_NUMERIC_FIELDS:
        return True
    
    # Check if any field in our sets matches after cleaning
    for numeric_field in ALL_NUMERIC_FIELDS:
        if clean_field_name(numeric_field) == cleaned_name:
            return True
    
    return False

def is_p_value_field(field_name: str) -> bool:
    """Check if a field is a p-value field requiring significance classification."""
    if not field_name:
        return False
    
    # Clean the field name first
    cleaned_name = clean_field_name(field_name)
    
    # Check direct match first
    if cleaned_name in P_VALUE_FIELDS:
        return True
    
    # Check if any field in our p-value set matches after cleaning
    for p_field in P_VALUE_FIELDS:
        if clean_field_name(p_field) == cleaned_name:
            return True
    
    return False

def classify_p_value_significance(value: str) -> str:
    """
    Classify p-value into significance categories.
    
    Rules:
    - p > 0.05 → "Non-Significant"
    - 0.001 < p ≤ 0.05 → "Significant" 
    - p ≤ 0.001 → "Highly Significant"
    
    Examples:
    - "p<0.05" → "Significant" (assuming p=0.049)
    - "p=0.001" → "Highly Significant"
    - "p>0.05" → "Non-Significant"
    - "Non-Significant" → "Non-Significant" (already classified)
    """
    if not value or not isinstance(value, str):
        return ""
    
    value = value.strip()
    
    # Handle empty or missing values
    if not value or value.lower() in ["", "not mentioned", "not available", "n/a", "na"]:
        return ""
    
    # If already classified, return as-is
    if value in ["Non-Significant", "Significant", "Highly Significant"]:
        return value
    
    # Handle already classified variations
    if value.lower() in ["non-significant", "not significant", "ns"]:
        return "Non-Significant"
    elif value.lower() in ["highly significant", "very significant"]:
        return "Highly Significant"
    elif value.lower() in ["significant", "sig"]:
        return "Significant"
    
    # Extract numeric p-value for classification
    # Handle formats like "p<0.05", "p=0.001", "p>0.05"
    p_value_match = re.search(r'p\s*([<>=])\s*(\d+(?:\.\d+)?)', value.lower())
    if p_value_match:
        operator = p_value_match.group(1)
        p_val = float(p_value_match.group(2))
        
        if operator == '>' and p_val >= 0.05:
            return "Non-Significant"
        elif operator == '<':
            if p_val <= 0.001:
                return "Highly Significant"
            elif p_val <= 0.05:
                return "Significant" 
            else:
                return "Non-Significant"
        elif operator == '=':
            if p_val > 0.05:
                return "Non-Significant"
            elif p_val <= 0.001:
                return "Highly Significant"
            else:
                return "Significant"
    
    # Handle direct numeric values
    numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
    if numeric_match:
        p_val = float(numeric_match.group(1))
        if p_val > 0.05:
            return "Non-Significant"
        elif p_val <= 0.001:
            return "Highly Significant"
        else:
            return "Significant"
    
    # If no numeric value found, return original
    logger.warning(f"Could not classify p-value significance from: '{value}'")
    return value

def extract_numeric_value(value: str) -> str:
    """
    Extract numeric value from various formats.
    
    Examples:
    - "45%" -> "45"
    - "0.05" -> "0.05"
    - "25.5 months" -> "25.5"
    - "10.8 Months" -> "10.8"
    - "NR" -> "NR"
    - "Not reached" -> "NR"
    - "12.0 (8.2–17.1)" -> "12.0"
    - "n (%) 7 (18)" -> "18"
    - "Months" -> ""
    - "Reference" -> ""
    """
    if not value or not isinstance(value, str):
        return ""
    
    value = value.strip()
    
    # Handle empty or missing values
    if not value or value.lower() in ["", "not mentioned", "not available", "n/a", "na"]:
        return ""
    
    # Handle pure text values that should be empty
    if value.lower() in ["months", "reference", "references", "not applicable", "not reported", "n/r"]:
        return ""
    
    # Handle "not reached" or "NR" cases
    if value.lower() in ["not reached", "nr", "not estimable", "ne"]:
        return "NR"
    
    # Handle format like "n (%) 7 (18)" - extract the percentage in parentheses
    percentage_match = re.search(r'n\s*\(%\).*?(\d+)\s*\((\d+(?:\.\d+)?)\)', value, re.IGNORECASE)
    if percentage_match:
        return percentage_match.group(2)
    
    # Handle confidence intervals like "12.0 (8.2–17.1)" - extract the main value
    ci_match = re.search(r'^(\d+(?:\.\d+)?)\s*\([\d\.\-–]+\)', value)
    if ci_match:
        return ci_match.group(1)
    
    # Handle percentage values like "45%" or "45.5%"
    percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', value)
    if percent_match:
        return percent_match.group(1)
    
    # Handle p-values like "p<0.05", "p=0.001", "p>0.05"
    p_value_match = re.search(r'p\s*[<>=]\s*(\d+(?:\.\d+)?)', value, re.IGNORECASE)
    if p_value_match:
        return p_value_match.group(1)
    
    # Handle hazard ratios like "HR=0.61", "HR: 0.61"
    hr_match = re.search(r'hr\s*[:=]\s*(\d+(?:\.\d+)?)', value, re.IGNORECASE)
    if hr_match:
        return hr_match.group(1)
    
    # Handle ranges like "20-30" - extract the first value
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*\d+(?:\.\d+)?', value)
    if range_match:
        return range_match.group(1)
    
    # Handle values with "months" or "years" like "25.5 months", "10.8 Months"
    time_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:months?|years?)', value, re.IGNORECASE)
    if time_match:
        return time_match.group(1)
    
    # Extract any numeric value (including decimals)
    numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
    if numeric_match:
        return numeric_match.group(1)
    
    # If no numeric value found, return empty string for numeric fields
    logger.warning(f"Could not extract numeric value from: '{value}' - returning empty string")
    return ""

def clean_numeric_field(field_name: str, value: Any) -> str:
    """
    Clean a field based on its type - numeric extraction or p-value classification.
    """
    if not isinstance(value, str):
        value = str(value) if value is not None else ""
    
    # Check if this is a p-value field requiring significance classification
    if is_p_value_field(field_name):
        return classify_p_value_significance(value)
    
    # Check if this field should be numeric using robust field checking
    if is_numeric_field(field_name):
        return extract_numeric_value(value)
    
    # For non-numeric fields, return as-is
    return value

def process_treatment_arm(arm_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all numeric and p-value fields in a treatment arm.
    """
    processed_arm = {}
    
    for field_name, value in arm_data.items():
        if is_p_value_field(field_name):
            processed_arm[field_name] = classify_p_value_significance(value)
            logger.debug(f"Processed p-value field '{field_name}': '{value}' -> '{processed_arm[field_name]}'")
        elif is_numeric_field(field_name):
            processed_arm[field_name] = clean_numeric_field(field_name, value)
            logger.debug(f"Processed numeric field '{field_name}': '{value}' -> '{processed_arm[field_name]}'")
        else:
            processed_arm[field_name] = value
    
    return processed_arm

def process_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all numeric fields in the extracted data.
    """
    if not data or "treatment_arms" not in data:
        return data
    
    processed_data = data.copy()
    
    # Process each treatment arm
    processed_arms = []
    for arm in data["treatment_arms"]:
        processed_arm = process_treatment_arm(arm)
        processed_arms.append(processed_arm)
    
    processed_data["treatment_arms"] = processed_arms
    
    logger.info(f"Processed numeric fields for {len(processed_arms)} treatment arms")
    return processed_data

def test_numeric_extraction():
    """Test function to verify numeric extraction works correctly."""
    test_cases = [
        ("45%", "45"),
        ("0.05", "0.05"),
        ("25.5 months", "25.5"),
        ("10.8 Months", "10.8"),
        ("NR", "NR"),
        ("Not reached", "NR"),
        ("12.0 (8.2–17.1)", "12.0"),
        ("n (%) 7 (18)", "18"),
        ("p<0.05", "0.05"),
        ("HR=0.61", "0.61"),
        ("20-30", "20"),
        ("", ""),
        ("Not mentioned", ""),
        ("Months", ""),
        ("Reference", ""),
        ("References", ""),
        ("16 months", "16"),
        ("27.4 Months", "27.4"),
        ("0.001", "0.001"),
        ("35", "35")
    ]
    
    print("Testing numeric extraction:")
    for input_val, expected in test_cases:
        result = extract_numeric_value(input_val)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_val}' -> '{result}' (expected: '{expected}')")

    # Summary
    passed = sum(1 for input_val, expected in test_cases if extract_numeric_value(input_val) == expected)
    total = len(test_cases)
    print(f"\nTest Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")

if __name__ == "__main__":
    test_numeric_extraction() 