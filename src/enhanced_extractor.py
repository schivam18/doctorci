import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import pandas as pd
import io

from src.chunk_templates import (
    get_arm_discovery_prompt,
    get_chunk_prompt,
    get_shared_chunk_prompt,
    CHUNK_FIELD_MAP
)

class EnhancedClinicalExtractor:
    """
    Enhanced clinical trial data extractor with three-stage architecture:
    1. Pre-validation
    2. Focused extraction  
    3. Post-processing validation
    
    Now includes chunked-prompt approach for improved accuracy and reduced hallucination
    """
    
    def __init__(self, keywords_file: str = "data/keywords_structure_enhanced.json"):
        self.logger = logging.getLogger(__name__)
        self.keywords_structure = self._load_keywords_structure(keywords_file)
        self.validation_rules = self.keywords_structure.get("validation_rules", {})
        self.controlled_vocabularies = self.validation_rules.get("controlled_vocabularies", {})
        
    def _load_keywords_structure(self, keywords_file: str) -> Dict[str, Any]:
        """Load the enhanced keywords structure"""
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Keywords file not found: {keywords_file}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in keywords file: {e}")
            return {}
    
    def pre_validate(self, publication_text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Stage 1: Pre-validation
        Validate critical fields and determine if publication can be processed
        """
        self.logger.info("Starting pre-validation...")
        
        validation_result = {
            "can_process": False,
            "nct_number": None,
            "treatment_arms_count": 0,
            "errors": [],
            "warnings": []
        }
        
        # Check for NCT number (critical field)
        nct_patterns = self.validation_rules.get("critical_fields", {}).get("nct_number", {}).get("extraction_patterns", [])
        nct_found = False
        
        for pattern in nct_patterns:
            matches = re.findall(pattern, publication_text, re.IGNORECASE)
            if matches:
                validation_result["nct_number"] = matches[0]
                nct_found = True
                break
        
        if not nct_found:
            validation_result["errors"].append("No NCT number found - cannot process")
            return False, validation_result
        
        # Count treatment arms with improved detection patterns
        arm_indicators = [
            r"arm\s+\d+",
            r"group\s+\d+", 
            r"cohort\s+\d+",
            r"treatment\s+arm",
            r"dose\s+level"
        ]
        
        arm_count = 0
        for pattern in arm_indicators:
            matches = re.findall(pattern, publication_text, re.IGNORECASE)
            arm_count = max(arm_count, len(matches))
        
        # If no arms found with basic patterns, try more sophisticated detection
        if arm_count == 0:
            # Look for treatment assignments with patient counts in methods section
            treatment_patterns = [
                r"(\w+)\s+every\s+\d+\s+weeks?\s*\(n=\d+\)",
                r"(\w+)\s*\(n=\d+\)",
                r"(\w+)\s+group\s*\(n=\d+\)"
            ]
            
            unique_treatments = set()
            for pattern in treatment_patterns:
                matches = re.findall(pattern, publication_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        treatment_name = match[0].lower()
                        # Filter out common non-treatment words
                        if treatment_name not in ['the', 'and', 'or', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'a', 'an']:
                            unique_treatments.add(treatment_name)
                    else:
                        treatment_name = match.lower()
                        if treatment_name not in ['the', 'and', 'or', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'a', 'an']:
                            unique_treatments.add(treatment_name)
            
            # Cap the arm count at a reasonable number (most trials have 1-6 arms)
            arm_count = min(len(unique_treatments), 6)
        
        validation_result["treatment_arms_count"] = arm_count
        validation_result["can_process"] = True
        
        self.logger.info(f"Pre-validation complete: NCT={validation_result['nct_number']}, Arms={arm_count}")
        return True, validation_result
    
    def create_focused_prompt(self, publication_text: str, validation_data: Dict[str, Any]) -> str:
        """
        Stage 2: Create focused extraction prompt
        Generate comprehensive prompt based on enhanced keywords structure
        """
        nct_number = validation_data.get("nct_number", "")
        arm_count = validation_data.get("treatment_arms_count", 0)
        
        # Generate comprehensive field list from keywords structure
        shared_fields = self._get_shared_fields()
        arm_fields = self._get_arm_fields()
        
        prompt = f"""
TASK: Extract comprehensive clinical trial data from this publication.

CRITICAL REQUIREMENTS:
1. NCT number: {nct_number} (already validated)
2. Expected treatment arms: {arm_count}
3. Output raw JSON only (no markdown, no explanations)
4. Extract ONLY explicit information - never infer or guess
5. Use empty string "" for missing values

TREATMENT ARMS:
- Each unique treatment = separate arm
- Different doses of same drug = separate arms  
- Combination therapies use "+" (e.g., "Drug A + Drug B")

DATA FORMATS:
- Numbers: Extract digits only (e.g., "25%" → "25")
- Survival: Months only (e.g., "12.5 months" → "12.5") 
- Binary: "YES" or "NO" only
- Missing: Use ""

COMPREHENSIVE JSON STRUCTURE:
{{
  "NCT Number": "{nct_number}",
  "Publication name": "Journal YYYY; Volume:Pages",
  "Publication Year": "YYYY",
  "PDF number": "filename",
  "Trial name": "Trial name or 'No Name'",
  "Sponsors": "Industry-Sponsored or non Industry-Sponsored",
  "Clinical Trial Phase": "Stage X",
  "Cancer Type": "Select from controlled list",
  "Primary endpoint": "text",
  "Secondary endpoint": "text",
  "Median Age": "number",
  "Mechanism of action": "text",
  "Target Protein": "text",
  "Type of therapy": "text",
  "Dosage": "text",
  "Type of dosing": "text",
  "Number of doses per year": "number",
  "Biomarker Inclusion": "YES/NO",
  "Biomarkers Inclusion Criteria": "text",
  "Biomarkers Exclusion Criteria": "text",
  "Major country where clinical trial is conducted": "text",
  "Study start date": "YYYY-MM-DD",
  "Study completion date": "YYYY-MM-DD",
  "First results": "YYYY-MM-DD",
  "Trial run in Europe": "YES/NO",
  "Trial run in US": "YES/NO",
  "Trial run in China": "YES/NO",
  "treatment_arms": [
    {{
      "Generic name": "Drug name or Drug A + Drug B",
      "Brand name": "text",
      "Line of Treatment": "Neoadjuvant/First Line/2nd Line/3rd Line+",
      "Number of patients": "number",
      "Company EU": "text",
      "Company US": "text",
      "Company China": "text",
      "Biosimilar": "YES/NO",
      "Chemotherapy Naive": "YES/NO",
      "Chemotherapy Failed": "YES/NO",
      "Immune Checkpoint Inhibitor (ICI) Naive": "YES/NO",
      "Immune Checkpoint Inhibitor (ICI) failed": "YES/NO",
      "Ipilimumab-failure or Ipilimumab-refractory": "YES/NO",
      "Anti PD-1/L1-failure or Anti PD-1/L1-refractory": "YES/NO",
      "Mutation status": "text",
      "BRAF-mutation": "YES/NO",
      "NRAS-Mutation": "YES/NO",
      "Objective response rate (ORR)": "percentage",
      "Complete Response (CR)": "percentage",
      "Pathological Complete Response (pCR)": "percentage",
      "Complete Metabolic Response (CMR)": "percentage",
      "Disease Control Rate or DCR": "percentage",
      "Clinical Benefit Rate (CBR)": "percentage",
      "Duration of Response (DOR) rate": "percentage",
      "Progression free survival (PFS) rate at 6 months": "percentage",
      "Progression free survival (PFS) rate at 9 months": "percentage",
      "Progression free survival (PFS) rate at 12 months": "percentage",
      "Progression free survival (PFS) rate at 18 months": "percentage",
      "Progression free survival (PFS) rate at 24 months": "percentage",
      "Progression free survival (PFS) rate at 48 months": "percentage",
      "Overall survival (OS) rate at 6 months": "percentage",
      "Overall survival (OS) rate at 9 months": "percentage",
      "Overall survival (OS) rate at 12 months": "percentage",
      "Overall survival (OS) rate at 18 months": "percentage",
      "Overall survival (OS) rate at 24 months": "percentage",
      "Overall survival (OS) rate at 48 months": "percentage",
      "Median Progression free survival (PFS)": "months",
      "Length of measuring PFS": "months",
      "p-value of PFS": "Non-Significant/Significant/Highly Significant",
      "Hazard ratio (HR) PFS": "decimal",
      "Median Overall survival (OS)": "months",
      "Length of measuring OS": "months",
      "p-value of OS": "Non-Significant/Significant/Highly Significant",
      "Hazard ratio (HR) OS": "decimal",
      "Event-Free Survival (EFS)": "months",
      "p-value of EFS": "Non-Significant/Significant/Highly Significant",
      "Hazard ratio (HR) EFS": "decimal",
      "Recurrence-Free Survival (RFS)": "months",
      "p-value of RFS": "Non-Significant/Significant/Highly Significant",
      "Length of measuring RFS": "months",
      "Hazard ratio (HR) RFS": "decimal",
      "Metastasis-Free Survival (MFS)": "months",
      "Length of measuring MFS": "months",
      "Hazard ratio (HR) MFS": "decimal",
      "Time to response (TTR)": "months",
      "Time to Progression (TTP)": "months",
      "Time to Next Treatment (TTNT)": "months",
      "Time to Treatment Failure (TTF)": "months",
      "Median Duration of response or DOR": "months",
      "Adverse events (AE)": "percentage",
      "Treatment emergent adverse events (TEAE)": "percentage",
      "Treatment-related adverse events (TRAE)": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher adverse events (AE)": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment emergent adverse events (TEAE)": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-related adverse events (TRAE)": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-emergent adverse events (TEAE)": "percentage",
      "Grade 4 treatment emergent adverse events": "percentage",
      "Grade 5 treatment emergent adverse events": "percentage",
      "Serious Adverse Events (SAE)": "percentage",
      "Serious treatment emergent adverse events": "percentage",
      "Serious treatment related adverse events": "percentage",
      "Treatment-emergent adverse events (TEAE) led to treatment discontinuation": "percentage",
      "Adverse events (AEs) leading to discontinuation": "percentage",
      "Treatment-emergent adverse events (TEAE) led to death": "percentage",
      "Adverse Events leading to death": "percentage",
      "Immune related adverse events (irAEs)": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Immune related adverse events (irAEs)": "percentage",
      "Cytokine Release Syndrome or CRS": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cytokine Release Syndrome or CRS": "percentage",
      "White blood cell (WBC) decreased": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thrombocytopenia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutropenia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Leukopenia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Anemia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutrophil count decreased": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 White blood cell (WBC) decreased": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Nausea": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Diarrhea": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Colitis": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Constipation": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Dyspnea": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cough": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonitis": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hyperglycemia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thyroiditis": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hypophysitis": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hepatitis": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Alanine aminotransferase": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pyrexia": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Bleeding": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pruritus": "percentage",
      "Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Rash": "percentage"
    }}
  ]
}}

EXTRACTION INSTRUCTIONS:
1. Extract ALL fields listed above that are explicitly mentioned in the publication
2. For percentages: extract number only (e.g., "25%" → "25")
3. For months: extract number only (e.g., "12.5 months" → "12.5")
4. For binary fields: use "YES" or "NO" only
5. For missing data: use empty string ""
6. For survival data with "not reached": use "NR"

PUBLICATION TEXT:
{publication_text[:60000]}  # Increased text length for comprehensive extraction

Return JSON only:"""
        
        return prompt
    
    def _get_shared_fields(self) -> List[str]:
        """Get list of shared fields from keywords structure"""
        shared_fields = []
        field_groups = self.keywords_structure.get("field_groups", {})
        
        for group_name, group_data in field_groups.items():
            if "fields" in group_data:
                for field in group_data["fields"]:
                    if isinstance(field, dict) and "name" in field:
                        shared_fields.append(field["name"])
        
        return shared_fields
    
    def _get_arm_fields(self) -> List[str]:
        """Get list of arm-specific fields from keywords structure"""
        arm_fields = []
        arm_specific = self.keywords_structure.get("arm_specific_fields", {})
        
        for category_name, category_data in arm_specific.items():
            if "fields" in category_data:
                for field in category_data["fields"]:
                    if isinstance(field, dict) and "name" in field:
                        arm_fields.append(field["name"])
            elif isinstance(category_data, dict):
                # Handle nested structures like efficacy_endpoints
                for subcategory_name, subcategory_data in category_data.items():
                    if "fields" in subcategory_data:
                        for field in subcategory_data["fields"]:
                            if isinstance(field, dict) and "name" in field:
                                arm_fields.append(field["name"])
        
        return arm_fields
    
    def validate_and_clean_data(self, raw_data: Dict[str, Any], validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Post-processing validation
        Validate and clean extracted data
        """
        self.logger.info("Starting post-processing validation...")
        
        validated_data = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "validation_status": "validated",
                "errors": [],
                "warnings": []
            },
            "data": raw_data
        }
        
        # Validate NCT number consistency
        expected_nct = validation_data.get("nct_number")
        extracted_nct = raw_data.get("nct_number")
        
        if expected_nct and extracted_nct and expected_nct != extracted_nct:
            validated_data["extraction_metadata"]["errors"].append(
                f"NCT number mismatch: expected {expected_nct}, got {extracted_nct}"
            )
        
        # Validate treatment arms
        arms = raw_data.get("arms", [])
        expected_arms = validation_data.get("treatment_arms_count", 0)
        
        if len(arms) != expected_arms and expected_arms > 0:
            validated_data["extraction_metadata"]["warnings"].append(
                f"Arm count mismatch: expected {expected_arms}, extracted {len(arms)}"
            )
        
        # Validate each treatment arm
        for i, arm in enumerate(arms):
            arm_errors = self._validate_treatment_arm(arm, i + 1)
            validated_data["extraction_metadata"]["errors"].extend(arm_errors)
        
        # Clean data formats
        validated_data["data"] = self._clean_data_formats(raw_data)
        
        # Update validation status
        if validated_data["extraction_metadata"]["errors"]:
            validated_data["extraction_metadata"]["validation_status"] = "errors_found"
        elif validated_data["extraction_metadata"]["warnings"]:
            validated_data["extraction_metadata"]["validation_status"] = "warnings_found"
        
        self.logger.info(f"Post-processing complete: {len(validated_data['extraction_metadata']['errors'])} errors, {len(validated_data['extraction_metadata']['warnings'])} warnings")
        return validated_data
    
    def _validate_treatment_arm(self, arm: Dict[str, Any], arm_number: int) -> List[str]:
        """Validate individual treatment arm"""
        errors = []
        
        # Check required fields
        required_fields = ["generic_name", "patients"]
        for field in required_fields:
            if not arm.get(field):
                errors.append(f"Arm {arm_number}: Missing required field '{field}'")
        
        # Validate patient count
        patients = arm.get("patients")
        if patients:
            try:
                patient_count = int(str(patients).replace(",", ""))
                if patient_count <= 0:
                    errors.append(f"Arm {arm_number}: Invalid patient count: {patients}")
            except ValueError:
                errors.append(f"Arm {arm_number}: Non-numeric patient count: {patients}")
        
        # Validate percentages
        percentage_fields = ["orr", "grade_3_plus_ae"]
        for field in percentage_fields:
            value = arm.get(field)
            if value and value != "":
                try:
                    percentage = float(str(value).replace("%", ""))
                    if percentage < 0 or percentage > 100:
                        errors.append(f"Arm {arm_number}: Invalid percentage for {field}: {value}")
                except ValueError:
                    if value not in ["NR", "not reached"]:
                        errors.append(f"Arm {arm_number}: Non-numeric percentage for {field}: {value}")
        
        return errors
    
    def _clean_data_formats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize data formats"""
        cleaned_data = data.copy()
        
        # Clean treatment arms
        if "arms" in cleaned_data:
            for arm in cleaned_data["arms"]:
                # Clean patient counts
                if "patients" in arm and arm["patients"]:
                    arm["patients"] = str(arm["patients"]).replace(",", "")
                
                # Clean percentages
                percentage_fields = ["orr", "grade_3_plus_ae", "median_pfs"]
                for field in percentage_fields:
                    if field in arm and arm[field]:
                        value = str(arm[field])
                        if "%" in value:
                            arm[field] = value.replace("%", "")
                        elif value.lower() in ["nr", "not reached"]:
                            arm[field] = "NR"
        
        return cleaned_data
    
    def detect_arms(self, publication_text: str) -> Dict[str, Any]:
        """
        Stage 1: Detect all treatment arms in the publication
        Returns prompt and metadata for external LLM processing
        """
        self.logger.info("Detecting treatment arms...")
        
        prompt = get_arm_discovery_prompt(publication_text)
        
        return {
            "prompt": prompt,
            "stage": "arm_discovery",
            "chunk_id": 0,
            "description": "Arm discovery - identifies all treatment arms"
        }

    def extract_tables_as_csv(self, publication_text: str) -> str:
        """
        Extract markdown tables and convert to CSV format for LLM processing
        """
        try:
            # Find all markdown tables
            table_pattern = r'\|.*?\|\n(?:\|.*?\|\n)+'
            tables = re.findall(table_pattern, publication_text, re.MULTILINE)
            
            csv_tables = []
            for i, table in enumerate(tables):
                try:
                    # Convert markdown table to CSV
                    lines = table.strip().split('\n')
                    # Remove separator lines (those with just | - | - |)
                    data_lines = [line for line in lines if not re.match(r'^\s*\|[\s\-\|]*\|\s*$', line)]
                    
                    # Convert to CSV format
                    csv_lines = []
                    for line in data_lines:
                        # Split by | and clean up
                        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove first/last empty
                        csv_lines.append(','.join(f'"{cell}"' for cell in cells))
                    
                    if csv_lines:
                        csv_tables.append(f"TABLE_{i+1}:\n" + '\n'.join(csv_lines))
                        
                except Exception as e:
                    self.logger.warning(f"Could not parse table {i+1}: {e}")
                    continue
            
            return '\n\n'.join(csv_tables)
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return ""

    def build_chunk_prompt(self, publication_text: str, arm: Optional[Dict], chunk_id: int) -> Dict[str, Any]:
        """
        Build prompt for specific chunk extraction
        Returns prompt and metadata for external LLM processing
        """
        # Extract tables for better data extraction
        tables_csv = self.extract_tables_as_csv(publication_text)
        
        # Chunks 1 and 10 are shared (publication-level)
        if chunk_id in [1, 10]:
            prompt = get_shared_chunk_prompt(publication_text, chunk_id, tables_csv)
            return {
                "prompt": prompt,
                "chunk_id": chunk_id,
                "chunk_type": "shared",
                "fields": CHUNK_FIELD_MAP[chunk_id],
                "description": f"Shared chunk {chunk_id} - publication-level data"
            }
        
        # Chunks 2-9 are arm-specific
        if arm is None:
            raise ValueError(f"Arm information required for chunk {chunk_id}")
            
        prompt = get_chunk_prompt(publication_text, arm, chunk_id, tables_csv)
        return {
            "prompt": prompt,
            "chunk_id": chunk_id,
            "chunk_type": "arm_specific",
            "arm_id": arm.get("arm_id"),
            "arm_name": arm.get("generic_name"),
            "fields": CHUNK_FIELD_MAP[chunk_id],
            "description": f"Arm-specific chunk {chunk_id} for arm {arm.get('arm_id')}"
        }

    def merge_chunk_results(self, arm_id: str, shared_data: Dict, arm_partials: List[Dict]) -> Dict:
        """
        Merge chunk results into final arm-level JSON
        """
        self.logger.info(f"Merging chunk results for arm {arm_id}")
        
        # Start with arm identification
        arm_json = {
            "arm_id": arm_id,
            **shared_data  # Add shared publication data
        }
        
        # Merge arm-specific chunks (later chunks override earlier for conflicts)
        for partial in arm_partials:
            if partial:  # Skip empty partials
                arm_json.update(partial)
        
        # Validate and clean the merged data
        return self._validate_arm_data(arm_json)

    def _validate_arm_data(self, arm_data: Dict) -> Dict:
        """
        Validate and clean arm-level data
        """
        # Basic validation rules
        if not arm_data.get("Generic name"):
            self.logger.warning(f"Arm {arm_data.get('arm_id')} missing generic name")
        
        # Validate patient count
        patients = arm_data.get("Number of patients")
        if patients:
            try:
                patient_count = int(str(patients).replace(",", ""))
                if patient_count <= 0:
                    self.logger.warning(f"Invalid patient count: {patients}")
            except ValueError:
                if patients not in ["", "NA"]:
                    self.logger.warning(f"Non-numeric patient count: {patients}")
        
        # Validate percentages (should be 0-100)
        percentage_fields = [field for field in arm_data.keys() if "rate" in field.lower() or "response" in field.lower()]
        for field in percentage_fields:
            value = arm_data.get(field)
            if value and value not in ["", "NA", "NR"]:
                try:
                    pct = float(str(value).replace("%", ""))
                    if pct < 0 or pct > 100:
                        self.logger.warning(f"Invalid percentage for {field}: {value}")
                except ValueError:
                    pass
        
        return arm_data

    def extract_with_chunked_approach(self, publication_text: str) -> Dict[str, Any]:
        """
        Complete chunked extraction pipeline
        Returns prompts and metadata for external LLM processing
        """
        self.logger.info("Starting chunked extraction approach")
        
        # Stage 1: Arm discovery
        arm_discovery = self.detect_arms(publication_text)
        
        # Prepare chunk prompts (to be processed externally)
        chunk_prompts = {
            "arm_discovery": arm_discovery,
            "shared_chunks": {},
            "arm_chunks": {},
            "extraction_metadata": {
                "approach": "chunked",
                "total_chunks": 11,
                "shared_chunks": [1, 10],
                "arm_chunks": [2, 3, 4, 5, 6, 7, 8, 9],
                "extraction_date": datetime.now().isoformat()
            }
        }
        
        # Build shared chunk prompts (chunks 1 and 10)
        for chunk_id in [1, 10]:
            chunk_prompts["shared_chunks"][chunk_id] = self.build_chunk_prompt(publication_text, None, chunk_id)
        
        # Placeholder for arm-specific chunks (will be built after arm discovery)
        chunk_prompts["arm_chunks"] = {
            "note": "These will be generated after arm discovery is processed",
            "chunks_per_arm": [2, 3, 4, 5, 6, 7, 8, 9],
            "total_chunks_per_arm": 8
        }
        
        return chunk_prompts

    def extract_with_comprehensive_approach(self, publication_text: str) -> Dict[str, Any]:
        """
        Complete comprehensive chunked extraction pipeline
        Returns prompts and metadata for external LLM processing
        """
        self.logger.info("Starting comprehensive chunked extraction approach")
        
        # Stage 1: Arm discovery
        arm_discovery = self.detect_arms(publication_text)
        
        # Prepare chunk prompts (to be processed externally)
        chunk_prompts = {
            "arm_discovery": arm_discovery,
            "shared_chunks": {},
            "arm_chunks": {},
            "extraction_metadata": {
                "approach": "comprehensive_chunked",
                "total_chunks": 11,
                "shared_chunks": [1, 10],
                "arm_chunks": [2, 3, 4, 5, 6, 7, 8, 9],
                "total_fields_available": sum(len(fields) for fields in CHUNK_FIELD_MAP.values() if fields),
                "extraction_date": datetime.now().isoformat()
            }
        }
        
        # Build shared chunk prompts (chunks 1 and 10)
        for chunk_id in [1, 10]:
            chunk_prompts["shared_chunks"][chunk_id] = self.build_chunk_prompt(publication_text, None, chunk_id)
        
        # Placeholder for arm-specific chunks (will be built after arm discovery)
        chunk_prompts["arm_chunks"] = {
            "note": "These will be generated after arm discovery is processed",
            "chunks_per_arm": [2, 3, 4, 5, 6, 7, 8, 9],
            "total_chunks_per_arm": 8
        }
        
        return chunk_prompts

    def _get_current_datetime(self) -> str:
        """Get current datetime as ISO string"""
        return datetime.now().isoformat()

    def extract_with_validation(self, publication_text: str) -> Dict[str, Any]:
        """
        Complete extraction pipeline with validation (backward compatibility)
        """
        # Stage 1: Pre-validation
        can_process, validation_data = self.pre_validate(publication_text)
        if not can_process:
            return {
                "error": "Publication failed pre-validation",
                "validation_data": validation_data
            }
        
        # Stage 2: Create focused prompt
        prompt = self.create_focused_prompt(publication_text, validation_data)
        
        # Stage 3: Extract data (this would be done by LLM)
        # For now, return the prompt for external processing
        return {
            "prompt": prompt,
            "validation_data": validation_data,
            "extraction_ready": True
        } 