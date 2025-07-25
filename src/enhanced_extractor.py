import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import time


class EnhancedClinicalExtractor:
    """
    Enhanced clinical trial data extractor with three-stage architecture:
    1. Pre-validation
    2. Focused extraction with improved prompts
    3. Post-processing validation
    
    Incorporates improved prompt guidelines, missing data protocols,
    and complete keyword coverage from enhanced JSON schema.
    """
    
    def __init__(self, keywords_file: str = "data/keywords_structure_enhanced.json"):
        self.logger = logging.getLogger(__name__)
        self.keywords_structure = self._load_keywords_structure(keywords_file)
        self.validation_rules = self.keywords_structure.get("validation_rules", {})
        self.controlled_vocabularies = self.validation_rules.get("controlled_vocabularies", {})
        
        # Load improved prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
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
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load improved prompt templates and rules"""
        return {
            "extraction_rules": self._get_extraction_rules(),
            "missing_data_protocol": self._get_missing_data_protocol(),
            "validation_rules": self._get_validation_rules()
        }
    
    def _get_extraction_rules(self) -> str:
        """Get improved extraction rules from enhanced prompts"""
        return """
EXTRACTION RULES (CRITICAL):
1. NCT Number: Must be present - terminate if missing
2. Treatment Arms: Each unique treatment = separate arm, different doses = separate arms
3. Publication Format: "Journal YYYY; Volume:Pages" (e.g., "NEJM 2017; 377:1345-56")
4. Line of Therapy: "Neoadjuvant", "First Line", "2nd Line", "3rd Line+" (no "or" variations)
5. Sponsors: "Industry-Sponsored" or "non Industry-Sponsored" only
6. Clinical Trial Phase: "Stage I", "Stage I/II", "Stage II", "Stage II/III", "Stage III", "Stage III/Stage IV", "Stage IV"

VALUE PARSING RULES:
- Percentages: Extract number only (25% → 25)
- Months: Extract number only (12.5 months → 12.5)
- "Not reached"/"NR": Keep as "NR"
- P-values: "Non-Significant" (p>0.05), "Significant" (p≤0.05 to p>0.001), "Highly Significant" (p≤0.001)
- Missing efficacy data: Use ""
- Missing safety data: Use "NA"

SAFETY EVENT CLASSIFICATIONS:
Three classes of Events: 1) Adverse events (AE), 2) Treatment-emergent Adverse Events (TEAE), 3) Treatment-related Adverse Events (TRAE)
Grade 3+ calculation: Extract reported "Grade 3+" if available, or sum individual grades (Grade 3 + Grade 4 + Grade 5)

TREATMENT ARM RULES:
- Each unique treatment = separate arm
- Different doses of same drug = separate arms (include dose in name: "Nivolumab 1mg/kg")
- Combination therapies: "Drug A + Drug B"  
- Label arms as "Treatment arm 1", "Treatment arm 2", etc.
"""
    
    def _get_missing_data_protocol(self) -> str:
        """Define missing data handling protocol"""
        return """
MISSING DATA PROTOCOL:
- Efficacy parameters: Use "" for missing values
- Safety parameters: Use "NA" for missing values  
- Zero values: Record as "0" (not missing)
- "No discontinuation occurred": Record as "0"
- "Less than 1%": Record as "1"
- "Less than 0.5%": Record as "0.5"
- For patient counts reported as "<1": Record as "0"
"""
    
    def _get_validation_rules(self) -> str:
        """Get validation rules for post-processing"""
        return """
VALIDATION RULES:
- Verify NCT number format: NCT########
- Check percentages are 0-100 range
- Ensure survival times are positive numbers or "NR"
- Validate controlled vocabularies
- Confirm treatment arm patient counts don't overlap
"""
    
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
        if not nct_patterns:
            # Fallback patterns
            nct_patterns = [
                r"NCT\d{8}",
                r"ClinicalTrials\.gov.*NCT\d{8}",
                r"Clinical trial information:.*NCT\d{8}"
            ]
        
        nct_found = False
        for pattern in nct_patterns:
            matches = re.findall(pattern, publication_text, re.IGNORECASE)
            if matches:
                # Extract just the NCT number part
                for match in matches:
                    nct_match = re.search(r"NCT\d{8}", match)
                    if nct_match:
                        validation_result["nct_number"] = nct_match.group()
                        nct_found = True
                        break
                if nct_found:
                    break
        
        if not nct_found:
            validation_result["errors"].append("No NCT number found - cannot process")
            return False, validation_result
        
        # Enhanced treatment arm detection
        arm_count = self._detect_treatment_arms(publication_text)
        validation_result["treatment_arms_count"] = arm_count
        validation_result["can_process"] = True
        
        self.logger.info(f"Pre-validation complete: NCT={validation_result['nct_number']}, Arms={arm_count}")
        return True, validation_result
    
    def _detect_treatment_arms(self, publication_text: str) -> int:
        """Enhanced treatment arm detection"""
        # Multiple detection methods
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
        
        # Enhanced detection: Look for treatment assignments with patient counts
        if arm_count == 0:
            treatment_patterns = [
                r"(\w+)\s+every\s+\d+\s+weeks?\s*\(n\s*=\s*\d+\)",
                r"(\w+)\s*\(n\s*=\s*\d+\)",
                r"(\w+)\s+group\s*\(n\s*=\s*\d+\)",
                r"(\w+)\s+arm\s*\(n\s*=\s*\d+\)"
            ]
            
            unique_treatments = set()
            for pattern in treatment_patterns:
                matches = re.findall(pattern, publication_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        treatment_name = match[0].lower()
                    else:
                        treatment_name = match.lower()
                    
                    # Filter out common non-treatment words
                    if treatment_name not in ['the', 'and', 'or', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'a', 'an', 'patients', 'total']:
                        unique_treatments.add(treatment_name)
            
            arm_count = min(len(unique_treatments), 6) if unique_treatments else 1
        
        return max(arm_count, 1)  # Ensure at least 1 arm
    
    def create_focused_prompt(self, publication_text: str, validation_data: Dict[str, Any]) -> str:
        """
        Stage 2: Create enhanced focused extraction prompt
        Generate comprehensive prompt based on improved guidelines
        """
        nct_number = validation_data.get("nct_number", "")
        arm_count = validation_data.get("treatment_arms_count", 0)
        
        # Build dynamic field structure from enhanced schema
        field_structure = self._build_enhanced_json_structure()
        extraction_rules = self.prompt_templates["extraction_rules"]
        missing_data_protocol = self.prompt_templates["missing_data_protocol"]
        
        prompt = f"""
TASK: Extract comprehensive clinical trial data from this publication.

CRITICAL REQUIREMENTS:
1. NCT number: {nct_number} (already validated)
2. Expected treatment arms: {arm_count}
3. Output raw JSON only (no markdown, no explanations)
4. Extract ONLY explicit information - never infer or guess

{extraction_rules}

{missing_data_protocol}

ENHANCED JSON STRUCTURE:
{field_structure}

PUBLICATION IDENTIFICATION:
- Must extract from most recent publication if multiple exist for same NCT
- Publication format: "Journal YYYY; Volume:Pages"

CONTROLLED VOCABULARIES:
Cancer Type: {', '.join(self.controlled_vocabularies.get('cancer_type', []))}
Clinical Trial Phase: {', '.join(self.controlled_vocabularies.get('clinical_trial_phase', []))}
Line of Treatment: {', '.join(self.controlled_vocabularies.get('line_of_treatment', []))}

EXTRACTION INSTRUCTIONS:
1. Extract ALL fields listed above that are explicitly mentioned in the publication
2. For percentages: extract number only (e.g., "25%" → "25")
3. For months: extract number only (e.g., "12.5 months" → "12.5")
4. For binary fields: use "YES" or "NO" only
5. For missing efficacy data: use ""
6. For missing safety data: use "NA"
7. For survival data with "not reached": use "NR"
8. For p-values: use "Non-Significant", "Significant", or "Highly Significant"

PUBLICATION TEXT:
{publication_text[:65000]}

Return JSON only:"""
        
        return prompt
    
    def _build_enhanced_json_structure(self) -> str:
        """Build dynamic JSON structure from enhanced schema"""
        # Core structure with all enhanced fields
        structure = """{
  "NCT Number": "NCT########",
  "Publication Name": "Journal YYYY; Volume:Pages",
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
  "Study start date": "YYYY-MM-DD",
  "Study completion date": "YYYY-MM-DD",
  "First results": "YYYY-MM-DD",
  "Trial run in Europe": "YES/NO",
  "Trial run in US": "YES/NO",
  "Trial run in China": "YES/NO",
  "treatment_arms": [
    {
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
      "PFS rate at 6 months": "percentage",
      "PFS rate at 9 months": "percentage",
      "PFS rate at 12 months or 1 year": "percentage",
      "PFS rate at 18 months": "percentage",
      "PFS rate at 24 months or 2 years": "percentage",
      "PFS rate at 36 months or 3 years": "percentage",
      "PFS rate at 48 months or 4 years": "percentage",
      "OS rate at 6 months": "percentage",
      "OS rate at 9 months": "percentage",
      "OS rate at 12 months or 1 year": "percentage",
      "OS rate at 18 months": "percentage",
      "OS rate at 24 months or 2 years": "percentage",
      "OS rate at 36 months or 3 years": "percentage",
      "OS rate at 48 months or 4 years": "percentage",
      "Median Progression free survival (PFS)": "months",
      "Length or duration of measuring median PFS": "months",
      "p-value of median PFS": "Non-Significant/Significant/Highly Significant",
      "Hazard ratio (HR) PFS": "decimal",
      "Median Overall survival (OS)": "months",
      "Length or duration of measuring median OS": "months",
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
      "Treatment-emergent adverse events (TEAE)": "percentage",
      "Treatment-related adverse events (TRAE)": "percentage",
      "Grade 3+ or Grade 3 higher AE": "percentage",
      "Grade 3+ or Grade 3 higher TEAE": "percentage",
      "Grade 3+ or Grade 3 higher TRAE": "percentage",
      "Grade 3 TEAE": "percentage",
      "Grade 4 TEAE": "percentage",
      "Grade 5 TEAE": "percentage",
      "Grade 3 TRAE": "percentage",
      "Grade 4 TRAE": "percentage",
      "Grade 5 TRAE": "percentage",
      "Serious AE": "percentage",
      "Serious TEAE": "percentage",
      "Serious TRAE": "percentage",
      "AE leading to discontinuation": "percentage",
      "TEAE led or leading to treatment discontinuation": "percentage",
      "TRAE led or leading to treatment discontinuation": "percentage",
      "AE led or leading to death": "percentage",
      "TEAE led or leading to death": "percentage",
      "TRAE led or leading to death": "percentage",
      "Immune related AE": "percentage",
      "Serious Immune related AE": "percentage",
      "Immune related TEAE": "percentage",
      "Immune related TRAE": "percentage",
      "Cytokine Release Syndrome or CRS": "percentage",
      "White blood cell (WBC) decreased": "percentage"
    }
  ]
}"""
        return structure
    
    def validate_and_clean_data(self, raw_data: Dict[str, Any], validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Enhanced post-processing validation
        Validate and clean extracted data with improved rules
        """
        self.logger.info("Starting enhanced post-processing validation...")
        
        validated_data = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "validation_status": "validated",
                "errors": [],
                "warnings": [],
                "prompt_version": "enhanced_2.1"
            },
            "data": raw_data
        }
        
        # Enhanced NCT validation
        self._validate_nct_format(raw_data, validated_data)
        
        # Enhanced treatment arm validation
        self._validate_treatment_arms_enhanced(raw_data, validation_data, validated_data)
        
        # Validate safety data consistency (NA protocol)
        self._validate_safety_data(raw_data, validated_data)
        
        # Validate controlled vocabularies
        self._validate_controlled_vocabularies(raw_data, validated_data)
        
        # Enhanced data cleaning with missing data protocol
        validated_data["data"] = self._clean_data_formats_enhanced(raw_data)
        
        # Update validation status
        self._update_validation_status(validated_data)
        
        self.logger.info(f"Enhanced validation complete: {len(validated_data['extraction_metadata']['errors'])} errors, {len(validated_data['extraction_metadata']['warnings'])} warnings")
        return validated_data
    
    def _validate_nct_format(self, raw_data: Dict[str, Any], validated_data: Dict[str, Any]) -> None:
        """Validate NCT number format"""
        nct_number = raw_data.get("NCT Number")
        if nct_number:
            if not re.match(r"^NCT\d{8}$", nct_number):
                validated_data["extraction_metadata"]["errors"].append(
                    f"Invalid NCT number format: {nct_number}"
                )
    
    def _validate_treatment_arms_enhanced(self, raw_data: Dict[str, Any], validation_data: Dict[str, Any], validated_data: Dict[str, Any]) -> None:
        """Enhanced treatment arm validation"""
        treatment_arms = raw_data.get("treatment_arms", [])
        expected_arms = validation_data.get("treatment_arms_count", 0)
        
        if len(treatment_arms) != expected_arms and expected_arms > 0:
            validated_data["extraction_metadata"]["warnings"].append(
                f"Arm count mismatch: expected {expected_arms}, extracted {len(treatment_arms)}"
            )
        
        # Validate each treatment arm
        for i, arm in enumerate(treatment_arms):
            arm_errors = self._validate_treatment_arm_enhanced(arm, i + 1)
            validated_data["extraction_metadata"]["errors"].extend(arm_errors)
    
    def _validate_treatment_arm_enhanced(self, arm: Dict[str, Any], arm_number: int) -> List[str]:
        """Enhanced individual treatment arm validation"""
        errors = []
        
        # Check required fields
        required_fields = ["Generic name", "Number of patients"]
        for field in required_fields:
            if not arm.get(field):
                errors.append(f"Arm {arm_number}: Missing required field '{field}'")
        
        # Validate patient count
        patients = arm.get("Number of patients")
        if patients and patients != "":
            try:
                patient_count = int(str(patients).replace(",", ""))
                if patient_count <= 0:
                    errors.append(f"Arm {arm_number}: Invalid patient count: {patients}")
            except ValueError:
                errors.append(f"Arm {arm_number}: Non-numeric patient count: {patients}")
        
        # Validate percentages
        percentage_fields = [
            "Objective response rate (ORR)", "Grade 3+ or Grade 3 higher AE",
            "Grade 3+ or Grade 3 higher TEAE", "Grade 3+ or Grade 3 higher TRAE"
        ]
        for field in percentage_fields:
            value = arm.get(field)
            if value and value != "" and value != "NA":
                try:
                    percentage = float(str(value).replace("%", ""))
                    if percentage < 0 or percentage > 100:
                        errors.append(f"Arm {arm_number}: Invalid percentage for {field}: {value}")
                except ValueError:
                    if value not in ["NR", "not reached"]:
                        errors.append(f"Arm {arm_number}: Non-numeric percentage for {field}: {value}")
        
        return errors
    
    def _validate_safety_data(self, raw_data: Dict[str, Any], validated_data: Dict[str, Any]) -> None:
        """Validate safety data follows NA protocol"""
        treatment_arms = raw_data.get("treatment_arms", [])
        
        for i, arm in enumerate(treatment_arms):
            # Check safety fields use "NA" for missing values (not empty string)
            safety_fields = [field for field in arm.keys() if any(safety_term in field.lower() 
                            for safety_term in ["ae", "teae", "trae", "adverse", "grade", "serious"])]
            
            for field in safety_fields:
                value = arm.get(field)
                if value == "":  # Should be "NA" for safety fields
                    validated_data["extraction_metadata"]["warnings"].append(
                        f"Arm {i+1}: Safety field '{field}' uses empty string instead of 'NA'"
                    )
    
    def _validate_controlled_vocabularies(self, raw_data: Dict[str, Any], validated_data: Dict[str, Any]) -> None:
        """Validate fields against controlled vocabularies"""
        controlled_vocabs = self.controlled_vocabularies
        
        # Validate Clinical Trial Phase
        phase = raw_data.get("Clinical Trial Phase")
        if phase and phase not in controlled_vocabs.get("clinical_trial_phase", []):
            validated_data["extraction_metadata"]["errors"].append(
                f"Invalid Clinical Trial Phase: {phase}"
            )
        
        # Validate Cancer Type
        cancer_type = raw_data.get("Cancer Type")
        if cancer_type and cancer_type not in controlled_vocabs.get("cancer_type", []):
            validated_data["extraction_metadata"]["errors"].append(
                f"Invalid Cancer Type: {cancer_type}"
            )
        
        # Validate Line of Treatment for each arm
        treatment_arms = raw_data.get("treatment_arms", [])
        for i, arm in enumerate(treatment_arms):
            line_of_treatment = arm.get("Line of Treatment")
            if line_of_treatment and line_of_treatment not in controlled_vocabs.get("line_of_treatment", []):
                validated_data["extraction_metadata"]["errors"].append(
                    f"Arm {i+1}: Invalid Line of Treatment: {line_of_treatment}"
                )
    
    def _clean_data_formats_enhanced(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced data cleaning with missing data protocol"""
        cleaned_data = data.copy()
        
        # Clean treatment arms
        if "treatment_arms" in cleaned_data:
            for arm in cleaned_data["treatment_arms"]:
                # Clean patient counts
                if "Number of patients" in arm and arm["Number of patients"]:
                    arm["Number of patients"] = str(arm["Number of patients"]).replace(",", "")
                
                # Clean percentages (remove % symbol if present)
                percentage_fields = [field for field in arm.keys() if any(term in field.lower() 
                                   for term in ["rate", "percentage", "orr", "dcr", "cbr"])]
                for field in percentage_fields:
                    value = arm.get(field)
                    if value and isinstance(value, str):
                        if "%" in value:
                            arm[field] = value.replace("%", "")
                        elif value.lower() in ["nr", "not reached"]:
                            arm[field] = "NR"
                
                # Clean survival times (remove units if present)
                survival_fields = [field for field in arm.keys() if any(term in field.lower() 
                                 for term in ["survival", "pfs", "os", "efs", "rfs", "mfs", "duration"])]
                for field in survival_fields:
                    value = arm.get(field)
                    if value and isinstance(value, str):
                        if "months" in value.lower():
                            # Extract numeric part
                            numeric_match = re.search(r"(\d+\.?\d*)", value)
                            if numeric_match:
                                arm[field] = numeric_match.group(1)
                        elif value.lower() in ["nr", "not reached"]:
                            arm[field] = "NR"
        
        return cleaned_data
    
    def _update_validation_status(self, validated_data: Dict[str, Any]) -> None:
        """Update validation status based on errors and warnings"""
        if validated_data["extraction_metadata"]["errors"]:
            validated_data["extraction_metadata"]["validation_status"] = "errors_found"
        elif validated_data["extraction_metadata"]["warnings"]:
            validated_data["extraction_metadata"]["validation_status"] = "warnings_found"
        else:
            validated_data["extraction_metadata"]["validation_status"] = "validated"
    
    def extract_with_enhanced_validation(self, publication_text: str, llm_client=None) -> Dict[str, Any]:
        """
        Complete enhanced extraction pipeline with validation
        Integrates with OpenAI client or returns prompt for external processing
        """
        # Stage 1: Pre-validation
        can_process, validation_data = self.pre_validate(publication_text)
        if not can_process:
            return {
                "error": "Publication failed pre-validation",
                "validation_data": validation_data
            }
        
        # Stage 2: Create enhanced focused prompt
        prompt = self.create_focused_prompt(publication_text, validation_data)
        
        # Stage 3: Optional LLM integration
        if llm_client:
            try:
                raw_extraction = llm_client.get_chat_completion([{"role": "user", "content": prompt}])
                extracted_data = json.loads(raw_extraction)
                
                # Stage 4: Enhanced validation and cleaning
                validated_result = self.validate_and_clean_data(extracted_data, validation_data)
                
                return {
                    "status": "success",
                    "data": validated_result,
                    "prompt_used": prompt,
                    "validation_metadata": validation_data
                }
            except Exception as e:
                return {
                    "error": f"Enhanced extraction failed: {str(e)}",
                    "prompt": prompt,
                    "validation_data": validation_data
                }
        else:
            # Return prompt for external processing
            return {
                "prompt": prompt,
                "validation_data": validation_data,
                "extraction_ready": True,
                "prompt_version": "enhanced_2.1"
            }
    
    def process_publication_batch(self, publications: List[str], llm_client=None) -> List[Dict[str, Any]]:
        """Process multiple publications with enhanced extraction"""
        results = []
        
        for i, pub_text in enumerate(publications):
            self.logger.info(f"Processing publication {i+1}/{len(publications)}")
            
            result = self.extract_with_enhanced_validation(pub_text, llm_client)
            result["publication_index"] = i
            results.append(result)
            
            # Add delay to prevent rate limiting
            if llm_client and i < len(publications) - 1:
                time.sleep(0.5)
        
        return results
