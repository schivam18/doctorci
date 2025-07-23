"""
Strategic QC Field Selection Module

This module defines field selection strategies for comprehensive quality control.
Fields are categorized by clinical importance and extraction complexity.
"""

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum

class FieldImportance(Enum):
    CRITICAL = "critical"      # Must be accurate for analysis validity
    HIGH = "high"             # Important for clinical decision making  
    MEDIUM = "medium"         # Useful but not critical
    LOW = "low"               # Nice to have

class ExtractionDifficulty(Enum):
    EASY = "easy"             # Clear patterns, high accuracy expected
    MEDIUM = "medium"         # Some ambiguity, moderate accuracy
    HARD = "hard"             # Complex patterns, lower accuracy expected

@dataclass
class QCFieldSpec:
    field_name: str
    importance: FieldImportance
    difficulty: ExtractionDifficulty
    validation_type: str
    tolerance: float
    category: str

class StrategicQCFieldSelector:
    """
    Strategic field selection for comprehensive QC validation.
    
    Selection Criteria:
    1. Clinical Importance (CRITICAL + HIGH priority)
    2. Extraction Difficulty (focus on HARD fields for validation)
    3. Field Type Diversity (cover all major categories)
    4. Statistical Significance (fields used in analysis)
    """
    
    def __init__(self):
        self.field_specs = self._define_field_specifications()
    
    def _define_field_specifications(self) -> Dict[str, QCFieldSpec]:
        """Define QC specifications for all fields based on clinical importance and extraction complexity."""
        
        specs = {}
        
        # === CRITICAL IDENTIFIERS ===
        specs["NCT Number"] = QCFieldSpec(
            "NCT Number", FieldImportance.CRITICAL, ExtractionDifficulty.EASY,
            "exact_match", 1.0, "identifier"
        )
        specs["Generic name"] = QCFieldSpec(
            "Generic name", FieldImportance.CRITICAL, ExtractionDifficulty.MEDIUM,
            "case_insensitive", 0.95, "identifier"
        )
        specs["PDF name"] = QCFieldSpec(
            "PDF name", FieldImportance.CRITICAL, ExtractionDifficulty.EASY,
            "exact_match", 1.0, "identifier"
        )
        
        # === CRITICAL TRIAL CHARACTERISTICS ===
        specs["Clinical Trial Phase"] = QCFieldSpec(
            "Clinical Trial Phase", FieldImportance.CRITICAL, ExtractionDifficulty.EASY,
            "exact_match", 1.0, "trial_design"
        )
        specs["Cancer Type"] = QCFieldSpec(
            "Cancer Type", FieldImportance.CRITICAL, ExtractionDifficulty.MEDIUM,
            "case_insensitive", 0.95, "trial_design"
        )
        specs["Line of Treatment"] = QCFieldSpec(
            "Line of Treatment", FieldImportance.CRITICAL, ExtractionDifficulty.MEDIUM,
            "case_insensitive", 0.90, "trial_design"
        )
        specs["Number of patients"] = QCFieldSpec(
            "Number of patients", FieldImportance.CRITICAL, ExtractionDifficulty.EASY,
            "exact_numeric", 1.0, "population"
        )
        
        # === PRIMARY EFFICACY ENDPOINTS ===
        specs["Objective response rate (ORR)"] = QCFieldSpec(
            "Objective response rate (ORR)", FieldImportance.CRITICAL, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.02, "efficacy"  # ±2%
        )
        specs["Progression free survival (PFS)"] = QCFieldSpec(
            "Progression free survival (PFS)", FieldImportance.CRITICAL, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.1, "efficacy"   # ±0.1 months
        )
        specs["Overall survival (OS)"] = QCFieldSpec(
            "Overall survival (OS)", FieldImportance.CRITICAL, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.1, "efficacy"   # ±0.1 months
        )
        specs["Complete Response (CR)"] = QCFieldSpec(
            "Complete Response (CR)", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.02, "efficacy"  # ±2%
        )
        specs["Disease Control Rate or DCR"] = QCFieldSpec(
            "Disease Control Rate or DCR", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.02, "efficacy"  # ±2%
        )
        
        # === STATISTICAL MEASURES ===
        specs["p-value of PFS"] = QCFieldSpec(
            "p-value of PFS", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.001, "statistics"
        )
        specs["Hazard ratio (HR) PFS"] = QCFieldSpec(
            "Hazard ratio (HR) PFS", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "statistics"
        )
        specs["p-value of OS"] = QCFieldSpec(
            "p-value of OS", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.001, "statistics"
        )
        specs["Hazard ratio (HR) OS"] = QCFieldSpec(
            "Hazard ratio (HR) OS", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "statistics"
        )
        
        # === SURVIVAL RATES AT TIMEPOINTS ===
        specs["Progression free survival (PFS) rate at 12 months"] = QCFieldSpec(
            "Progression free survival (PFS) rate at 12 months", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "survival_rates"  # ±5%
        )
        specs["Overall survival (OS) rate at 12 months"] = QCFieldSpec(
            "Overall survival (OS) rate at 12 months", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "survival_rates"  # ±5%
        )
        specs["Progression free survival (PFS) rate at 24 months"] = QCFieldSpec(
            "Progression free survival (PFS) rate at 24 months", FieldImportance.HIGH, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "survival_rates"  # ±5%
        )
        
        # === PRIMARY SAFETY ENDPOINTS ===
        specs["Adverse events (AE)"] = QCFieldSpec(
            "Adverse events (AE)", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.05, "safety"    # ±5%
        )
        specs["Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher adverse events (AE)"] = QCFieldSpec(
            "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher adverse events (AE)", FieldImportance.CRITICAL, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.02, "safety"    # ±2%
        )
        specs["Serious Adverse Events (SAE)"] = QCFieldSpec(
            "Serious Adverse Events (SAE)", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.02, "safety"    # ±2%
        )
        specs["Treatment-emergent adverse events (TEAE) led to treatment discontinuation"] = QCFieldSpec(
            "Treatment-emergent adverse events (TEAE) led to treatment discontinuation", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.02, "safety"    # ±2%
        )
        specs["Adverse Events leading to death"] = QCFieldSpec(
            "Adverse Events leading to death", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.01, "safety"    # ±1%
        )
        
        # === SPECIFIC SAFETY EVENTS ===
        specs["Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutropenia"] = QCFieldSpec(
            "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutropenia", FieldImportance.MEDIUM, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.03, "specific_safety"
        )
        specs["Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Diarrhea"] = QCFieldSpec(
            "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Diarrhea", FieldImportance.MEDIUM, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.03, "specific_safety"
        )
        specs["Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonitis"] = QCFieldSpec(
            "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonitis", FieldImportance.MEDIUM, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.02, "specific_safety"
        )
        
        # === SECONDARY EFFICACY ===
        specs["Pathological Complete Response (pCR)"] = QCFieldSpec(
            "Pathological Complete Response (pCR)", FieldImportance.MEDIUM, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.03, "secondary_efficacy"
        )
        specs["Clinical Benefit Rate (CBR)"] = QCFieldSpec(
            "Clinical Benefit Rate (CBR)", FieldImportance.MEDIUM, ExtractionDifficulty.MEDIUM,
            "numeric_tolerance", 0.03, "secondary_efficacy"
        )
        specs["Duration of Response (DOR) rate"] = QCFieldSpec(
            "Duration of Response (DOR) rate", FieldImportance.MEDIUM, ExtractionDifficulty.HARD,
            "numeric_tolerance", 0.05, "secondary_efficacy"
        )
        
        # === TRIAL METADATA ===
        specs["Primary endpoint"] = QCFieldSpec(
            "Primary endpoint", FieldImportance.HIGH, ExtractionDifficulty.EASY,
            "text_similarity", 0.80, "metadata"
        )
        specs["Secondary endpoint"] = QCFieldSpec(
            "Secondary endpoint", FieldImportance.MEDIUM, ExtractionDifficulty.EASY,
            "text_similarity", 0.75, "metadata"
        )
        specs["Mechanism of action"] = QCFieldSpec(
            "Mechanism of action", FieldImportance.MEDIUM, ExtractionDifficulty.MEDIUM,
            "text_similarity", 0.70, "metadata"
        )
        specs["Target Protein"] = QCFieldSpec(
            "Target Protein", FieldImportance.MEDIUM, ExtractionDifficulty.MEDIUM,
            "text_similarity", 0.80, "metadata"
        )
        
        # === YES/NO FIELDS ===
        specs["Listed in NCCN guidelines"] = QCFieldSpec(
            "Listed in NCCN guidelines", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "exact_match", 1.0, "binary"
        )
        specs["Immune Checkpoint Inhibitor (ICI) Naive"] = QCFieldSpec(
            "Immune Checkpoint Inhibitor (ICI) Naive", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "exact_match", 1.0, "binary"
        )
        specs["BRAF-mutation"] = QCFieldSpec(
            "BRAF-mutation", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "exact_match", 1.0, "binary"
        )
        specs["Biomarker Inclusion"] = QCFieldSpec(
            "Biomarker Inclusion", FieldImportance.HIGH, ExtractionDifficulty.MEDIUM,
            "exact_match", 1.0, "binary"
        )
        
        return specs
    
    def get_tier1_fields(self) -> List[str]:
        """Get Tier 1 QC fields (CRITICAL importance)."""
        return [field for field, spec in self.field_specs.items() 
                if spec.importance == FieldImportance.CRITICAL]
    
    def get_tier2_fields(self) -> List[str]:
        """Get Tier 2 QC fields (HIGH importance)."""
        return [field for field, spec in self.field_specs.items() 
                if spec.importance == FieldImportance.HIGH]
    
    def get_tier3_fields(self) -> List[str]:
        """Get Tier 3 QC fields (MEDIUM importance)."""
        return [field for field, spec in self.field_specs.items() 
                if spec.importance == FieldImportance.MEDIUM]
    
    def get_comprehensive_qc_fields(self) -> List[str]:
        """Get comprehensive QC field list (Tier 1 + Tier 2 + selected Tier 3)."""
        tier1 = self.get_tier1_fields()
        tier2 = self.get_tier2_fields()
        tier3 = self.get_tier3_fields()
        
        # Return all tiers for comprehensive validation
        return tier1 + tier2 + tier3
    
    def get_field_spec(self, field_name: str) -> QCFieldSpec:
        """Get field specification for validation."""
        return self.field_specs.get(field_name)
    
    def get_fields_by_category(self, category: str) -> List[str]:
        """Get fields by category."""
        return [field for field, spec in self.field_specs.items() 
                if spec.category == category]
    
    def get_validation_summary(self) -> Dict[str, int]:
        """Get summary of field counts by importance and category."""
        summary = {
            "total_fields": len(self.field_specs),
            "critical": len(self.get_tier1_fields()),
            "high": len(self.get_tier2_fields()),
            "medium": len(self.get_tier3_fields()),
            "by_category": {}
        }
        
        categories = set(spec.category for spec in self.field_specs.values())
        for category in categories:
            summary["by_category"][category] = len(self.get_fields_by_category(category))
        
        return summary

# Initialize global selector
QC_FIELD_SELECTOR = StrategicQCFieldSelector()

# Export comprehensive QC fields list
COMPREHENSIVE_QC_KEYWORDS = QC_FIELD_SELECTOR.get_comprehensive_qc_fields()

# Export tiered field lists  
TIER1_QC_KEYWORDS = QC_FIELD_SELECTOR.get_tier1_fields()  # Critical
TIER2_QC_KEYWORDS = QC_FIELD_SELECTOR.get_tier2_fields()  # High  
TIER3_QC_KEYWORDS = QC_FIELD_SELECTOR.get_tier3_fields()  # Medium 