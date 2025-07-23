# src/therapy_classifier.py
from typing import Dict, List

THERAPY_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "Immune Checkpoint Inhibitors": {
        "approved": ["Pembrolizumab", "Nivolumab", "Ipilimumab", "Relatlimab"],
        "unapproved": ["Triple checkpoint blockade", "new antibodies"]
    },
    "Cellular Therapy": {
        "approved": ["Lifileucel", "Amtagvi", "TIL therapy"],
        "unapproved": ["CAR T-cell therapy"]
    },
    "Targeted Therapy": {
        "approved": ["Vemurafenib", "Dabrafenib", "Trametinib", "Encorafenib"],
        "unapproved": ["Next-gen BRAF/MEK inhibitors", "new combos"]
    },
    "Oncolytic Virus Therapy": {
        "approved": ["Talimogene laherparepvec", "Imlygic"],
        "unapproved": ["Other viral vectors"]
    },
    "Chemotherapy": {
        "approved": ["Dacarbazine"],
        "unapproved": ["Temozolomide", "Fotemustine"]
    },
    "Bispecific Antibodies": {
        "approved": ["Tebentafusp-tebn", "Kimmtrak"],
        "unapproved": ["Other bispecifics in trial"]
    },
    "Vaccine/Immunostimulant": {
        "approved": [],
        "unapproved": ["Cancer vaccines", "immunostimulants"]
    }
}

def classify_therapy(generic_name: str) -> str:
    """
    Classifies the therapy type based on the generic drug name.

    Args:
        generic_name: The generic name of the drug or combination.

    Returns:
        The classified therapy type, or "Unknown" if not found.
    """
    if not generic_name or not isinstance(generic_name, str):
        return "Unknown"

    # Split combinations and check each drug
    drug_names = [name.strip().lower() for name in generic_name.split('+')]

    for drug in drug_names:
        for category, sub_categories in THERAPY_CATEGORIES.items():
            for status, drug_list in sub_categories.items():
                if any(known_drug.lower() in drug for known_drug in drug_list):
                    return category
    
    return "Unknown" 