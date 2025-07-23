"""
Comprehensive post-processing module for clinical trial data.
Handles all validation, formatting, and business rules while maintaining arm-specific structure.
"""

import re
from typing import Any, Dict, List, Optional
import logging

from src.numeric_field_processor import process_treatment_arm, classify_p_value_significance
from src.therapy_classifier import classify_therapy

logger = logging.getLogger(__name__)

# Validation constants based on user prompts
VALID_STAGES = {
    "Stage I", "Stage I/II", "Stage II", "Stage II/III", 
    "Stage III", "Stage III/Stage IV", "Stage IV"
}

VALID_CANCER_TYPES = {
    "Resected Cutaneous Melanoma",
    "Unresectable Cutaneous Melanoma", 
    "Cutaneous melanoma with Brain metastasis",
    "Cutaneous Melanoma with CNS metastasis",
    "Uveal Melanoma",
    "Mucosal Melanoma",
    "Acral Melanoma",
    "Basal Cell Carcinoma",
    "Merkel Cell Carcinoma",
    "Cutaneous Squamous Cell Carcinoma"
}

VALID_LINE_OF_TREATMENT = {
    "Neoadjuvant",
    "First Line or Untreated", 
    "2nd Line",
    "3rd Line+"
}

VALID_NCCN_PREFERENCES = {
    "Preferred Regimen",
    "Other recommended regimens", 
    "useful in certain circumstances",
    "Not Recommended",
    "Not applicable (Not listed in NCCN guidelines)"
}

TRIAL_NAME_PATTERNS = ["keynote", "checkmate", "masterkey"]

def validate_stage(stage: str) -> str:
    """Validate and standardize stage according to 8-class requirement."""
    if not stage or not isinstance(stage, str):
        return ""
    
    stage = stage.strip()
    
    # Direct match
    for valid_stage in VALID_STAGES:
        if stage.lower() == valid_stage.lower():
            return valid_stage
    
    # Pattern matching for variations
    stage_lower = stage.lower()
    
    if "stage i/ii" in stage_lower or "stage 1/2" in stage_lower:
        return "Stage I/II"
    elif "stage ii/iii" in stage_lower or "stage 2/3" in stage_lower:
        return "Stage II/III"  
    elif "stage iii/iv" in stage_lower or "stage 3/4" in stage_lower:
        return "Stage III/Stage IV"
    elif "stage iv" in stage_lower or "stage 4" in stage_lower:
        return "Stage IV"
    elif "stage iii" in stage_lower or "stage 3" in stage_lower:
        return "Stage III"
    elif "stage ii" in stage_lower or "stage 2" in stage_lower:
        return "Stage II"
    elif "stage i" in stage_lower or "stage 1" in stage_lower:
        return "Stage I"
    
    logger.warning(f"Stage validation failed for: '{stage}' - not in valid 8 classes")
    return stage  # Return original if no match

def validate_cancer_type(cancer_type: str) -> str:
    """Validate and standardize cancer type to predefined categories."""
    if not cancer_type or not isinstance(cancer_type, str):
        return ""
    
    cancer_lower = cancer_type.lower().strip()
    
    # Valid cancer types
    valid_types = {
        "resected cutaneous melanoma": "Resected Cutaneous Melanoma",
        "unresectable cutaneous melanoma": "Unresectable Cutaneous Melanoma", 
        "cutaneous melanoma with brain metastasis": "Cutaneous melanoma with Brain metastasis",
        "cutaneous melanoma with brain metastases": "Cutaneous melanoma with Brain metastasis",
        "cutaneous melanoma with cns metastasis": "Cutaneous Melanoma with CNS metastasis",
        "cutaneous melanoma with cns metastases": "Cutaneous Melanoma with CNS metastasis",
        "uveal melanoma": "Uveal Melanoma",
        "mucosal melanoma": "Mucosal Melanoma", 
        "acral melanoma": "Acral Melanoma",
        "basal cell carcinoma": "Basal Cell Carcinoma",
        "merkel cell carcinoma": "Merkel Cell Carcinoma",
        "cutaneous squamous cell carcinoma": "Cutaneous Squamous Cell Carcinoma"
    }
    
    # Direct match
    if cancer_lower in valid_types:
        return valid_types[cancer_lower]
    
    # Partial matches for melanoma with brain metastasis
    if "melanoma" in cancer_lower and ("brain" in cancer_lower or "cns" in cancer_lower):
        if "brain" in cancer_lower:
            return "Cutaneous melanoma with Brain metastasis"
        elif "cns" in cancer_lower:
            return "Cutaneous Melanoma with CNS metastasis"
    
    # Partial matches for unresectable melanoma
    if "melanoma" in cancer_lower and "unresectable" in cancer_lower:
        return "Unresectable Cutaneous Melanoma"
    
    # Partial matches for resected melanoma
    if "melanoma" in cancer_lower and ("resected" in cancer_lower or "surgically removed" in cancer_lower):
        return "Resected Cutaneous Melanoma"
    
    # Generic melanoma fallback
    if cancer_lower == "melanoma":
        logger.warning(f"Cancer type validation failed for: '{cancer_type}' - not in valid 10 classes")
        return cancer_type  # Return original instead of empty string
    
    # Check for other specific types
    for key, value in valid_types.items():
        if key in cancer_lower:
            return value
    
    logger.warning(f"Cancer type validation failed for: '{cancer_type}' - not in valid 10 classes")
    return cancer_type  # Return original instead of empty string

def validate_line_of_treatment(line: str) -> str:
    """Validate and standardize line of treatment according to 4-class requirement."""
    if not line or not isinstance(line, str):
        return ""
    
    line = line.strip()
    
    # Direct match
    for valid_line in VALID_LINE_OF_TREATMENT:
        if line.lower() == valid_line.lower():
            return valid_line
    
    # Pattern matching for variations
    line_lower = line.lower()
    
    if any(term in line_lower for term in ["neoadjuvant", "neo-adjuvant"]):
        return "Neoadjuvant"
    elif any(term in line_lower for term in ["first line", "1st line", "first-line", "untreated", "treatment-naive", "naive"]):
        return "First Line or Untreated"
    elif any(term in line_lower for term in ["second line", "2nd line", "second-line", "previously treated"]):
        return "2nd Line"
    elif any(term in line_lower for term in ["third line", "3rd line", "third-line", "3rd line+", "heavily pretreated"]):
        return "3rd Line+"
    
    logger.warning(f"Line of treatment validation failed for: '{line}' - not in valid 4 classes")
    return line  # Return original if no match

def validate_nccn_preference(preference: str) -> str:
    """Validate and standardize NCCN preference according to a comprehensive classification system."""
    if not preference or not isinstance(preference, str):
        return "Not applicable (Not listed in NCCN guidelines)"
    
    preference = preference.strip()
    pref_lower = preference.lower()
    
    # Handle "Not applicable" case first
    if pref_lower in ["not applicable", "n/a", "not listed", "not mentioned", ""]:
        return "Not applicable (Not listed in NCCN guidelines)"
    
    # Pattern matching for variations
    if "preferred" in pref_lower:
        return "Preferred Regimen"
    elif "not recommended" in pref_lower:
        return "Not Recommended"
    elif "other recommended" in pref_lower or "recommended" in pref_lower:
        return "Other recommended regimens"
    elif "useful" in pref_lower or "certain circumstances" in pref_lower:
        return "useful in certain circumstances"
    
    # Direct match for completeness
    for valid_pref in VALID_NCCN_PREFERENCES:
        if pref_lower == valid_pref.lower():
            return valid_pref
    
    logger.warning(f"NCCN preference validation failed for: '{preference}' - could not map to a valid class")
    return preference  # Return original if no match

def format_publication_name(pub_name: str) -> str:
    """Format publication name to strict 'Journal YEAR; Volume:StartPage-EndPage' format."""
    import re
    if not pub_name or not isinstance(pub_name, str):
        return ""
    pub_name = pub_name.strip()
    # Remove copyright and extraneous info
    pub_name = re.sub(r'© \d{4} by [^.]*\.?', '', pub_name)
    pub_name = re.sub(r'© \d{4} [^.]*\.?', '', pub_name)
    pub_name = pub_name.strip(' .')

    # Normalize journal names
    journal_map = {
        r'new england journal.*|n engl j med': 'NEJM',
        r'lancet oncology|lancet oncol': 'Lancet Oncol',
        r'lancet': 'Lancet',
        r'journal of clinical oncology|j clin oncol': 'JCO',
    }
    journal = None
    for pattern, abbr in journal_map.items():
        if re.search(pattern, pub_name, re.IGNORECASE):
            journal = abbr
            break
    # Patterns for extraction
    patterns = [
        # NEJM 2017; 377:1345-56
        (r'(\d{4}).*?(\d+)[;:, ]+([\d]+)[–-]([\d]+)', 'NEJM'),
        # Lancet 2017; 390:1853-62
        (r'(\d{4}).*?(\d+)[;:, ]+([\d]+)[–-]([\d]+)', 'Lancet'),
        # JCO 2017; 36:1658-1667
        (r'(\d{4}).*?(\d+)[;:, ]+([\d]+)[–-]([\d]+)', 'JCO'),
        # Lancet Oncol 2012; 13:459-65
        (r'(\d{4}).*?(\d+)[;:, ]+([\d]+)[–-]([\d]+)', 'Lancet Oncol'),
    ]
    # Try to match known journals
    if journal:
        # Try to extract year, volume, start, end
        m = re.search(r'(\d{4}).*?(\d+)[;:, ]+([\d]+)[–-]([\d]+)', pub_name)
        if m:
            year, volume, start, end = m.groups()
            # Remove decimals from page numbers
            start = start.split('.')[0]
            end = end.split('.')[0]
            return f"{journal} {year}; {volume}:{start}-{end}"
    # Fallback: try to extract any journal/year/volume/pages
    m = re.search(r'([A-Za-z .]+)[,;]? (\d{4})[;:, ]+(\d+)[;:, ]+([\d]+)[–-]([\d]+)', pub_name)
    if m:
        j, year, volume, start, end = m.groups()
        j = j.strip().replace('Journal of Clinical Oncology', 'JCO').replace('New England Journal of Medicine', 'NEJM').replace('Lancet Oncology', 'Lancet Oncol').replace('Lancet', 'Lancet')
        start = start.split('.')[0]
        end = end.split('.')[0]
        return f"{j} {year}; {volume}:{start}-{end}"
    # If already in correct format, return as-is
    if re.match(r'^[A-Za-z ]+ \d{4}; \d+:\d+-\d+$', pub_name):
        return pub_name
    # If no pattern matches, return cleaned original
    return pub_name

def detect_trial_name(trial_name: str, full_text: str = "") -> str:
    """Detect trial name patterns (Keynote, Checkmate, Masterkey) or return 'No Name'."""
    if not trial_name or not isinstance(trial_name, str):
        trial_name = ""
    
    # Check trial_name field first
    trial_lower = trial_name.lower()
    
    for pattern in TRIAL_NAME_PATTERNS:
        if pattern in trial_lower:
            # Extract the specific trial name (e.g., "Keynote-006")
            match = re.search(f'{pattern}[-\\s]?(\\d+[a-z]*)', trial_lower)
            if match:
                return f"{pattern.capitalize()}-{match.group(1)}"
            else:
                return f"{pattern.capitalize()}"
    
    # If not found in trial_name, check full_text if provided
    if full_text:
        text_lower = full_text.lower()
        for pattern in TRIAL_NAME_PATTERNS:
            match = re.search(f'{pattern}[-\\s]?(\\d+[a-z]*)', text_lower)
            if match:
                return f"{pattern.capitalize()}-{match.group(1)}"
    
    return "No Name"

def process_discontinuation_text(value: str) -> str:
    """Process discontinuation text patterns to convert to numeric values."""
    if not value or not isinstance(value, str):
        return ""
    
    value_lower = value.lower().strip()
    
    # Pattern: "No treatment discontinuation occurred due to TEAE" → "0"
    no_discontinuation_patterns = [
        "no treatment discontinuation occurred",
        "no discontinuation",
        "no patients discontinued", 
        "0 patients discontinued",
        "zero patients discontinued"
    ]
    
    for pattern in no_discontinuation_patterns:
        if pattern in value_lower:
            return "0"
    
    return value  # Return original if no pattern matches

def classify_research_sponsor(sponsor: str) -> str:
    """Classify research sponsor into Industry-Sponsored or non Industry-Sponsored."""
    if not sponsor or not isinstance(sponsor, str):
        return ""
    
    sponsor_lower = sponsor.lower().strip()
    
    # If sponsor is "None" → "non Industry-Sponsored"
    if sponsor_lower in ["none", "n/a", "not applicable", ""]:
        return "non Industry-Sponsored"
    
    # Anything else → "Industry-Sponsored"
    return "Industry-Sponsored"

def format_generic_name(generic_name: str) -> str:
    """Ensure proper formatting of drug combinations with + separator."""
    if not generic_name or not isinstance(generic_name, str):
        return ""
    
    # Already has + separator
    if "+" in generic_name:
        # Clean up spacing around +
        parts = [part.strip() for part in generic_name.split("+")]
        return " + ".join(parts)
    
    # Look for other separators and convert
    for sep in [" and ", " & ", "/", ","]:
        if sep in generic_name:
            parts = [part.strip() for part in generic_name.split(sep)]
            return " + ".join(parts)
    
    return generic_name.strip()

def process_safety_data(value: str, field_name: str) -> str:
    """Process safety data fields to handle both numeric and text-based values."""
    if not value or not isinstance(value, str):
        return ""
    
    value = value.strip()
    
    # If it's already a number, return as-is
    if value.replace('.', '').replace('%', '').isdigit():
        return value
    
    # For percentage fields, try to extract numbers
    if '%' in value:
        # Extract percentage numbers
        import re
        numbers = re.findall(r'(\d+(?:\.\d+)?)', value)
        if numbers:
            return numbers[0]  # Return first number found
    
    # For adverse events that are text descriptions, return as-is for now
    # These will be processed by the numeric processor later
    return value

def process_shared_fields(shared_data: Dict[str, Any], full_text: str = "") -> Dict[str, Any]:
    """Process and validate shared fields (apply once per publication)."""
    processed = shared_data.copy()
    
    # Format publication name
    if "Publication name" in processed:
        processed["Publication name"] = format_publication_name(processed["Publication name"])
    
    # Detect trial name
    if "Trial name" in processed:
        processed["Trial name"] = detect_trial_name(processed["Trial name"], full_text)
    
    # Process NCCN fields
    if "Listed in NCCN guidelines" in processed:
        # Convert to YES/NO format
        nccn_value = processed["Listed in NCCN guidelines"]
        if isinstance(nccn_value, str):
            nccn_lower = nccn_value.lower().strip()
            if nccn_lower in ["yes", "true", "1"]:
                processed["Listed in NCCN guidelines"] = "YES"
            elif nccn_lower in ["no", "false", "0", ""]:
                processed["Listed in NCCN guidelines"] = "NO"
    
    if "Preference according to NCCN" in processed:
        processed["Preference according to NCCN"] = validate_nccn_preference(processed["Preference according to NCCN"])
    
    # Classify research sponsor (if it exists in shared fields)
    if "Sponsors" in processed:
        processed["Research Sponsor Type"] = classify_research_sponsor(processed["Sponsors"])
    
    return processed

def process_arm_specific_fields(arm_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate arm-specific fields (apply per treatment arm)."""
    processed = arm_data.copy()
    
    # Validate categorical fields
    if "Stage" in processed:
        processed["Stage"] = validate_stage(processed["Stage"])
    
    if "Cancer Type" in processed:
        processed["Cancer Type"] = validate_cancer_type(processed["Cancer Type"])
    
    if "Line of Treatment" in processed:
        processed["Line of Treatment"] = validate_line_of_treatment(processed["Line of Treatment"])
    
    if "Preference according to NCCN" in processed:
        processed["Preference according to NCCN"] = validate_nccn_preference(processed["Preference according to NCCN"])
    
    # Format generic name
    if "Generic name" in processed:
        processed["Generic name"] = format_generic_name(processed["Generic name"])
    
    # Classify therapy type based on generic name
    if "Generic name" in processed:
        processed["Type of therapy"] = classify_therapy(processed["Generic name"])
    
    # Process safety data fields
    safety_fields = [
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
        "Adverse Events leading to death"
    ]
    
    for field in safety_fields:
        if field in processed:
            processed[field] = process_safety_data(processed[field], field)
    
    # Process discontinuation text patterns
    discontinuation_fields = [
        "Treatment-emergent adverse events (TEAE) led to treatment discontinuation",
        "Adverse events (AEs) leading to discontinuation"
    ]
    
    for field in discontinuation_fields:
        if field in processed:
            processed[field] = process_discontinuation_text(processed[field])
    
    # Apply numeric field processing (includes p-value classification)
    processed = process_treatment_arm(processed)
    
    return processed

def process_extracted_data(raw_data: Dict[str, Any], full_text: str = "") -> Dict[str, Any]:
    """
    Comprehensive post-processing of extracted data.
    Maintains proper shared vs arm-specific field structure.
    """
    if not raw_data:
        return raw_data
    
    processed_data = {}
    
    # Process shared fields (once per publication)
    shared_fields = {k: v for k, v in raw_data.items() if k != "treatment_arms"}
    processed_data.update(process_shared_fields(shared_fields, full_text))
    
    # Process treatment arms (each arm individually)
    treatment_arms = raw_data.get("treatment_arms", [])
    processed_arms = []
    
    for arm in treatment_arms:
        processed_arm = process_arm_specific_fields(arm)
        processed_arms.append(processed_arm)
    
    processed_data["treatment_arms"] = processed_arms
    
    logger.info(f"Post-processing completed. Processed {len(processed_arms)} treatment arms.")
    return processed_data 