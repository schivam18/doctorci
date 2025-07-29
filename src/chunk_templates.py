"""
Enhanced chunk-based prompt templates with comprehensive field coverage
"""

# Comprehensive field mappings for 11 chunks
CHUNK_FIELD_MAP = {
    1: [  # Publication and trial metadata (shared)
        "Publication Name", "Publication Year", "PDF number", "Trial name", "Cancer Type", 
        "Generic name", "Brand name", "Company EU", "Company US", "Company China", 
        "Sponsors", "Clinical Trial Phase", "Chemotherapy Naive", "Chemotherapy Failed",
        "Immune Checkpoint Inhibitor (ICI) Naive", "Immune Checkpoint Inhibitor (ICI) failed",
        "Ipilimumab-failure or Ipilimumab-refractory", "Anti PD-1/L1-failure or Anti PD-1/L1-refractory",
        "Mutation status", "BRAF-mutation", "NRAS-Mutation", "Biosimilar", "Line of Treatment",
        "NCT Number", "Mechanism of action", "Target Protein", "Type of therapy", "Dosage",
        "Type of dosing", "Number of doses per year", "Primary endpoint", "Secondary endpoint",
        "Median Age", "Biomarker Inclusion", "Biomarkers Inclusion Criteria", "Biomarkers Exclusion Criteria",
        "Study start date", "Study completion date", "First results", "Trial run in Europe",
        "Trial run in US", "Trial run in China"
    ],
    2: [  # Patient demographics and basic info (arm-specific)
        "Number of patients", "Cancer Type", "Median Age", "Chemotherapy Naive", "Chemotherapy Failed",
        "Immune Checkpoint Inhibitor (ICI) Naive", "Immune Checkpoint Inhibitor (ICI) failed",
        "Ipilimumab-failure or Ipilimumab-refractory", "Anti PD-1/L1-failure or Anti PD-1/L1-refractory",
        "BRAF-mutation", "NRAS-Mutation", "Mutation status", "Biosimilar"
    ],
    3: [  # Treatment details (arm-specific)
        "Generic name", "Brand name", "Company EU", "Company US", "Company China",
        "Mechanism of action", "Target Protein", "Type of therapy", "Dosage", "Type of dosing",
        "Number of doses per year", "Line of Treatment", "Primary endpoint", "Secondary endpoint"
    ],
    4: [  # Survival endpoints (arm-specific)
        "Median Progression free survival (PFS)", "Length or duration of measuring median PFS",
        "p-value of median PFS", "Hazard ratio (HR) PFS", "Median Overall survival (OS)",
        "Length or duration of measuring median OS", "p-value of OS", "Hazard ratio (HR) OS",
        "Event-Free Survival (EFS)", "p-value of EFS", "Hazard ratio (HR) EFS",
        "Recurrence-Free Survival (RFS)", "p-value of RFS", "Length of measuring RFS",
        "Hazard ratio (HR) RFS", "Metastasis-Free Survival (MFS)", "Length of measuring MFS",
        "Hazard ratio (HR) MFS"
    ],
    5: [  # Time-based endpoints (arm-specific)
        "Time to response (TTR)", "Time to Progression (TTP)", "Time to Next Treatment (TTNT)",
        "Time to Treatment Failure (TTF)", "Median Duration of response or DOR",
        "Duration of Response (DOR) rate"
    ],
    6: [  # Efficacy endpoints (arm-specific)
        "Objective response rate (ORR)", "Complete Response (CR)", "Pathological Complete Response (pCR)",
        "Complete Metabolic Response (CMR)", "Disease Control Rate or DCR", "Clinical Benefit Rate (CBR)",
        "PFS rate at 6 months", "PFS rate at 9 months", "PFS rate at 12 months or 1 year",
        "PFS rate at 18 months", "PFS rate at 24 months or 2 years", "PFS rate at 36 months or 3 years",
        "PFS rate at 48 months or 4 years", "OS rate at 6 months", "OS rate at 9 months",
        "OS rate at 12 months or 1 year", "OS rate at 18 months", "OS rate at 24 months or 2 years",
        "OS rate at 36 months or 3 years", "OS rate at 48 months or 4 years"
    ],
    7: [  # Safety header - detect ONE class (AE/TEAE/TRAE) and extract general categories
        "safety_event_class", "Number of patients",
        "Adverse events (AE)", "Grade 3+ or Grade 3 higher AE", "AE leading to discontinuation", "Serious AE", "Immune related AE", "Serious Immune related AE", "AE led or leading to death",
        "Treatment-emergent adverse events (TEAE)", "Grade 3+ or Grade 3 higher TEAE", "Grade 3 TEAE", "Grade 4 TEAE", "Grade 5 TEAE", "TEAE led or leading to treatment discontinuation", "TEAE led or leading to death", "Serious TEAE", "Immune related TEAE",
        "Treatment-related adverse events (TRAE)", "Grade 3+ or Grade 3 higher TRAE", "Grade 3 TRAE", "Grade 4 TRAE", "Grade 5 TRAE", "TRAE led or leading to treatment discontinuation", "TRAE led or leading to death", "Immune related TRAE", "Serious TRAE",
        "Cytokine Release Syndrome or CRS", "White blood cell (WBC) decreased"
    ],
    8: [  # Grade 3+ specific events - AE class
        "Grade 3+ or Grade 3 higher \"AE\" Immune related adverse events (irAEs)",
        "Grade 3+ or Grade 3 higher \"AE\" Cytokine Release Syndrome or CRS",
        "Grade 3+ or Grade 3 higher \"AE\" Thrombocytopenia", "Grade 3+ or Grade 3 higher \"AE\" Neutropenia",
        "Grade 3+ or Grade 3 higher \"AE\" Leukopenia", "Grade 3+ or Grade 3 higher \"AE\" Nausea",
        "Grade 3+ or Grade 3 higher \"AE\" Anemia", "Grade 3+ or Grade 3 higher \"AE\" Diarrhea",
        "Grade 3+ or Grade 3 higher \"AE\" Colitis", "Grade 3+ or Grade 3 higher \"AE\" Hyperglycemia",
        "Grade 3+ or Grade 3 higher \"AE\" Neutrophil count decreased", "Grade 3+ or Grade 3 higher \"AE\" Dyspnea",
        "Grade 3+ or Grade 3 higher \"AE\" Pyrexia", "Grade 3+ or Grade 3 higher \"AE\" Bleeding",
        "Grade 3+ or Grade 3 higher \"AE\" Pruritus", "Grade 3+ or Grade 3 higher \"AE\" Rash",
        "Grade 3+ or Grade 3 higher \"AE\" Pneumonia", "Grade 3+ or Grade 3 higher \"AE\" Thyroiditis",
        "Grade 3+ or Grade 3 higher \"AE\" Hypophysitis", "Grade 3+ or Grade 3 higher \"AE\" Hepatitis",
        "Grade 3+ or Grade 3 higher \"AE\" Pneumonitis", "Grade 3+ or Grade 3 higher \"AE\" Alanine aminotransferase",
        "Grade 3+ or Grade 3 higher \"AE\" White blood cell (WBC) decreased"
    ],
    9: [  # Grade 3+ specific events - TRAE and TEAE classes
        "Grade 3+ or Grade 3 higher \"TRAE\" Immune related adverse events (irAEs)",
        "Grade 3+ or Grade 3 higher \"TRAE\" Cytokine Release Syndrome or CRS",
        "Grade 3+ or Grade 3 higher \"TRAE\" Thrombocytopenia", "Grade 3+ or Grade 3 higher \"TRAE\" Neutropenia",
        "Grade 3+ or Grade 3 higher \"TRAE\" Leukopenia", "Grade 3+ or Grade 3 higher \"TRAE\" Nausea",
        "Grade 3+ or Grade 3 higher \"TRAE\" Anemia", "Grade 3+ or Grade 3 higher \"TRAE\" Diarrhea",
        "Grade 3+ or Grade 3 higher \"TRAE\" Colitis", "Grade 3+ or Grade 3 higher \"TRAE\" Hyperglycemia",
        "Grade 3+ or Grade 3 higher \"TRAE\" Neutrophil count decreased", "Grade 3+ or Grade 3 higher \"TRAE\" Dyspnea",
        "Grade 3+ or Grade 3 higher \"TRAE\" Pyrexia", "Grade 3+ or Grade 3 higher \"TRAE\" Bleeding",
        "Grade 3+ or Grade 3 higher \"TRAE\" Pruritus", "Grade 3+ or Grade 3 higher \"TRAE\" Rash",
        "Grade 3+ or Grade 3 higher \"TRAE\" Pneumonia", "Grade 3+ or Grade 3 higher \"TRAE\" Thyroiditis",
        "Grade 3+ or Grade 3 higher \"TRAE\" Hypophysitis", "Grade 3+ or Grade 3 higher \"TRAE\" Pneumonitis",
        "Grade 3+ or Grade 3 higher \"TRAE\" Alanine aminotransferase", "Grade 3+ or Grade 3 higher \"TRAE\" Hepatitis",
        "Grade 3+ or Grade 3 higher \"TRAE\" White blood cell (WBC) decreased",
        "Grade 3+ or Grade 3 higher \"TEAE\" Immune related adverse events (irAEs)",
        "Grade 3+ or Grade 3 higher \"TEAE\" Cytokine Release Syndrome or CRS",
        "Grade 3+ or Grade 3 higher \"TEAE\" Thrombocytopenia", "Grade 3+ or Grade 3 higher \"TEAE\" Neutropenia",
        "Grade 3+ or Grade 3 higher \"TEAE\" Leukopenia", "Grade 3+ or Grade 3 higher \"TEAE\" Nausea",
        "Grade 3+ or Grade 3 higher \"TEAE\" Anemia", "Grade 3+ or Grade 3 higher \"TEAE\" Diarrhea",
        "Grade 3+ or Grade 3 higher \"TEAE\" Colitis", "Grade 3+ or Grade 3 higher \"TEAE\" Hyperglycemia",
        "Grade 3+ or Grade 3 higher \"TEAE\" Neutrophil count decreased", "Grade 3+ or Grade 3 higher \"TEAE\" Dyspnea",
        "Grade 3+ or Grade 3 higher \"TEAE\" Pyrexia", "Grade 3+ or Grade 3 higher \"TEAE\" Bleeding",
        "Grade 3+ or Grade 3 higher \"TEAE\" Pruritus", "Grade 3+ or Grade 3 higher \"TEAE\" Rash",
        "Grade 3+ or Grade 3 higher \"TEAE\" Pneumonia", "Grade 3+ or Grade 3 higher \"TEAE\" Thyroiditis",
        "Grade 3+ or Grade 3 higher \"TEAE\" Hypophysitis", "Grade 3+ or Grade 3 higher \"TEAE\" Hepatitis",
        "Grade 3+ or Grade 3 higher \"TEAE\" Pneumonitis"
    ],
    10: [  # Additional metadata (shared)
        "Publication Name", "Publication Year", "PDF number", "Trial name", "Cancer Type",
        "Sponsors", "Clinical Trial Phase", "NCT Number", "Study start date", "Study completion date",
        "First results", "Trial run in Europe", "Trial run in US", "Trial run in China",
        "Biomarker Inclusion", "Biomarkers Inclusion Criteria", "Biomarkers Exclusion Criteria"
    ]
}

def get_arm_discovery_prompt(publication_text: str) -> str:
    """Generate prompt for arm discovery with comprehensive backbone rules"""
    
    return f"""
SYSTEM: You are a precise clinical data extractor. Temperature 0. Never guess.

CRITICAL BACKBONE RULES:
1. **Treatment Arms**: Each arm is a separate treatment (monotherapy or combination). There can be one arm, two arms, three arms, or even more. Each arm is a separate treatment, whether its monotherapy or combination of two therapies or of three therapies.

2. **NCT Number**: Must be present and unique per trial. Format: NCT########. Every publication should have a NCT number. If no NCT is mentioned, don't retrieve any information.

3. **Generic Name**: Each cell should be a treatment (whether its single, combo or triplet). If it's a combo it should explicitly show both drugs with a + in the middle. For dose variations, include the dose: "Nivolumab 1mg/kg", "Nivolumab 3mg/kg", "Nivolumab 10mg/kg"

4. **Trial Name**: Only if "Keynote", "Checkmate", or "Masterkey". Otherwise "No Name"

5. **Patient Count**: Each arm must have specific patient count. Don't combine all arms in one clinical trial and sum the patient numbers.

6. **IGNORE**: Maintenance phases, crossover treatments, post-progression treatments

7. **ARM ISOLATION**: Each arm should have unique efficacy and safety parameters. The ORR, CR or DCR and even all the Safety parameters should be unique to the treatment arm.

8. **ARM-SPECIFIC DATA**: Each unique treatment arm should have the corresponding efficacy and safety. Cannot show values like (1, 2, 0) in one cell - This could mean there are multiple treatment arms within the trial.

DISCOVER all treatment arms in this publication. Return JSON only.

OUTPUT JSON STRUCTURE:
{{
  "treatment_arms": [
    {{
      "arm_id": "A1",
      "generic_name": "Drug Name or Drug A + Drug B",
      "number_of_patients": "count",
      "nct_number": "NCT########",
      "trial_name": "Trial Name or No Name"
    }}
  ]
}}

PUBLICATION TEXT:
{publication_text[:55000]}
"""

def get_shared_chunk_prompt(publication_text: str, chunk_id: int, tables_csv: str = "") -> str:
    """Generate prompt for shared publication-level chunks with backbone rules"""
    
    fields = CHUNK_FIELD_MAP.get(chunk_id, [])
    if not fields:
        return ""
    
    # Backbone rules for publication-level fields
    backbone_rules = """
BACKBONE RULES:
**Publication Name**: Format as "Name of Journal - Year - Volume - Pages" (e.g., "NEJM 2017; 377:1345-56"). Journal names can be: Lancet, NEJM, JCO and similar.
**Cancer Type**: Only 10 classes: Resected Cutaneous Melanoma, Unresectable Cutaneous Melanoma, Cutaneous melanoma with Brain metastasis, Cutaneous Melanoma with CNS metastasis, Uveal Melanoma, Mucosal Melanoma, Acral Melanoma, Basal Cell Carcinoma, Merkel Cell Carcinoma, Cutaneous Squamous Cell Carcinoma
**Clinical Trial Phase**: Only 8 classes: Stage I, Stage I/II, Stage II, Stage II/III, Stage III, Stage III/Stage IV, Stage IV. Look for explicit mentions like "phase 2", "phase II", "Stage II", "stage 2" in the text. If you see "phase 2" or "stage 2", use "Stage II".
**Sponsors**: If company name → "Industry-Sponsored", if "None" → "non Industry-Sponsored"
**Trial Name**: Only if "Keynote", "Checkmate", or "Masterkey". Otherwise "No Name"
**NCT Number**: Must be present. Format: NCT########. Every publication should have a NCT number.
**Date Formats**: Convert to YYYY-MM-DD format (e.g., "September 16, 2013" → "2013-09-16")
**Biomarker Inclusion**: If mentioned → "Yes", otherwise ""
**Biomarkers Inclusion/Exclusion Criteria**: Extract exact text as mentioned
**Line of Therapy**: Only 4 classes: Neoadjuvant, First Line, 2nd Line, 3rd Line+
**Type of Therapy**: Classify as Immune Checkpoint Inhibitors, Cellular Therapy, Targeted Therapy, Oncolytic Virus Therapy, Chemotherapy, Bispecific Antibodies, or Vaccine/Immunostimulant
**Efficacy Values**: Only one value per cell. Extract percentages from parentheses: n (%) 7 (18) → 18
**PFS/OS Values**: In months only. "12.0 (8.2–17.1)" → 12.0
**"Not reached" or "NR"**: Output as "NR"
**P-value Classification**:
- Non-Significant: p > 0.05
- Significant: p ≤ 0.05 to p > 0.001  
- Highly Significant: p ≤ 0.001
**Value Extraction**: Extract numbers from parentheses ( ). Examples: 
- 125 (45%) → 45
- 51 (54) → 54 (for safety data without % symbol)
- 86 (91) → 91 (for safety data without % symbol)
**Safety Data Format**: In tables, extract the percentage value in parentheses, not the patient count outside parentheses
**ARM-SPECIFIC SAFETY**: Each arm must have its own unique safety data. Do NOT copy safety data from other arms.
**PDF number**: Extract from filename programmatically
**Generic name**: Each cell should be a treatment (whether its single, combo or triplet). If it's a combo it should explicitly show both drugs with a + in the middle. For dose variations, include the dose: "Nivolumab 1mg/kg"
**Number of patients**: Each treatment should have a specific number of patients being tested in that arm. Don't combine all arms in one clinical trial and sum the patient numbers.
**Objective response rate (ORR)**: Extract percentage from parentheses. If listed as "n (%) 7 (18)", extract "18"
**Complete Response (CR)**: Extract percentage from parentheses
**Disease Control Rate or DCR**: Extract percentage from parentheses
**Median Duration of response or DOR**: In months only, or "NR" if not reached
**Duration of Response (DOR) rate**: Extract percentage from parentheses
**Median Progression free survival (PFS)**: In months only, or "NR" if not reached
**Median Overall survival (OS)**: In months only, or "NR" if not reached
**Event-Free Survival (EFS)**: In months only, or "NR" if not reached
**Recurrence-Free Survival (RFS)**: In months only, or "NR" if not reached
**Metastasis-Free Survival (MFS)**: In months only, or "NR" if not reached
**Time to response (TTR)**: In months only, or "NR" if not reached
**Time to Progression (TTP)**: In months only, or "NR" if not reached
**Time to Next Treatment (TTNT)**: In months only, or "NR" if not reached
**Time to Treatment Failure (TTF)**: In months only, or "NR" if not reached
**PFS rate at X months**: Extract percentage from parentheses
**OS rate at X months**: Extract percentage from parentheses
**Adverse events (AE)**: Extract percentage from parentheses
**Treatment-emergent adverse events (TEAE)**: Extract percentage from parentheses
**Treatment-related adverse events (TRAE)**: Extract percentage from parentheses
**Grade 3+ calculations**: If grades 3, 4, 5 are shown separately, sum them: X + Y + Z = Grade 3+ value
**Missing data protocol**: Use "NA" if no value found, "0" for "<1", "1" for "<1%", "0.5" for "<0.5%"
**Discontinuations**: If "No treatment discontinuation occurred", use "0"
"""

    field_list = "\n".join([f'"{field}": ""' for field in fields])
    
    tables_section = ""
    if tables_csv:
        tables_section = f"""
### TABLES FOR EXTRACTION ###
{tables_csv}
"""

    return f"""
SYSTEM: You are a precise clinical data extractor. Temperature 0. Never guess.

EXTRACT publication-level fields (shared across all arms).

If a field is not explicitly stated, output "".
Return JSON only with this EXACT structure:
{{
  "treatment_arms": [
    {{
{field_list}
    }}
  ]
}}

{backbone_rules}

{tables_section}

PUBLICATION TEXT:
{publication_text[:55000]}
"""

def get_chunk_prompt(publication_text: str, arm: dict, chunk_id: int, tables_csv: str = "") -> str:
    """Generate prompt for specific chunk extraction with enhanced safety handling and backbone rules"""
    
    fields = CHUNK_FIELD_MAP.get(chunk_id, [])
    if not fields:
        return ""
    
    # Enhanced safety instructions for safety chunks
    safety_instructions = ""
    if chunk_id in [7, 8, 9]:
        safety_instructions = """
CRITICAL SAFETY EXTRACTION RULES:
1. FIRST: Detect which safety class is reported for this arm - ONLY ONE of these three:
   - Adverse events (AE)
   - Treatment-emergent Adverse Events (TEAE) 
   - Treatment-related Adverse Events (TRAE)
2. Fill "safety_event_class" with the detected class (AE, TEAE, or TRAE)
3. ONLY extract data for the detected class - ignore the other two completely
4. Grade 3+ calculation: If grades 3, 4, 5 are shown separately, sum them: X + Y + Z = Grade 3+ value
5. VALUE EXTRACTION FROM TABLES: Extract percentage values from parentheses ( ). Examples:
   - "125 (45%)" → extract "45" (the percentage, not the patient count)
   - "97 (31)" → extract "31" (the percentage, not the patient count)
   - "51 (54)" → extract "54" (the percentage, not the patient count)
   - "86 (91)" → extract "91" (the percentage, not the patient count)
   - "10 (11)" → extract "11" (the percentage, not the patient count)
   - "44 (47)" → extract "47" (the percentage, not the patient count)
   - "3 (3.2)" → extract "3.2" (the percentage, not the patient count)
   - "43 (93)" → extract "93" (the percentage, not the patient count)
   - "11 (24)" → extract "24" (the percentage, not the patient count)
6. Missing data protocol:
   - Use "NA" if no value found
   - For "less than 1%" or "<1%": use "1"
   - For "No discontinuation occurred": use "0"
   - For patient counts "<1": use "0"
   - For percentages "less than 0.5%": use "0.5"
7. Extract percentages as numbers only (25% → 25)
8. Focus on tables for specific adverse event data
9. ARM ISOLATION: Only extract data specific to this arm, not other arms
10. SAFETY CLASS DETECTION: Look for explicit mentions like:
    - "Adverse events (AE)" or "AE" → safety_event_class = "AE"
    - "Treatment-emergent adverse events" or "TEAE" → safety_event_class = "TEAE"  
    - "Treatment-related adverse events" or "TRAE" → safety_event_class = "TRAE"
11. TABLE DATA EXTRACTION: When reading safety tables, always extract the percentage value in parentheses, not the patient count outside parentheses
12. ARM-SPECIFIC DATA: Each arm must have its own unique safety data. Do NOT copy safety data from other arms.
13. PERCENTAGE EXTRACTION: Always look for the percentage value in parentheses. If you see "n (%)" format, extract the percentage number.
14. CRITICAL: Never extract the patient count (number before parentheses). Always extract the percentage (number in parentheses).
15. SAFETY CLASS RULE: Only applicable for the table & There will be only one of these 3 (AE, TEAE, or TRAE).
"""

    # Comprehensive backbone rules
    backbone_rules = """
BACKBONE RULES:
**ARM ISOLATION**: Each arm should have unique efficacy and safety parameters. Do NOT mix data between arms. Each arm must have its own specific patient count, ORR, CR, DCR, and safety data.
**Publication Name**: Format as "Journal Year; Volume:Pages" (e.g., "N Engl J Med 2015;372:2006-17")
**Cancer Type**: Only 10 classes: Resected Cutaneous Melanoma, Unresectable Cutaneous Melanoma, Cutaneous melanoma with Brain metastasis, Cutaneous Melanoma with CNS metastasis, Uveal Melanoma, Mucosal Melanoma, Acral Melanoma, Basal Cell Carcinoma, Merkel Cell Carcinoma, Cutaneous Squamous Cell Carcinoma
**Clinical Trial Phase**: Only 8 classes: Stage I, Stage I/II, Stage II, Stage II/III, Stage III, Stage III/Stage IV, Stage IV. Look for explicit mentions like "phase 2", "phase II", "Stage II" in the text.
**Sponsors**: If company name → "Industry-Sponsored", if "None" → "non Industry-Sponsored"
**Efficacy Values**: Only one value per cell. Extract percentages from parentheses: n (%) 7 (18) → 18
**PFS/OS Values**: In months only. "12.0 (8.2–17.1)" → 12.0
**"Not reached" or "NR"**: Output as "NR"
**P-value Classification**:
- Non-Significant: p > 0.05
- Significant: p ≤ 0.05 to p > 0.001  
- Highly Significant: p ≤ 0.001
**Type of Therapy**: Classify as Immune Checkpoint Inhibitors, Cellular Therapy, Targeted Therapy, Oncolytic Virus Therapy, Chemotherapy, Bispecific Antibodies, or Vaccine/Immunostimulant
**Line of Therapy**: Only 4 classes (Neoadjuvant, First Line, 2nd Line, 3rd Line+)
**Value Extraction**: Extract numbers from parentheses ( ). Examples: 
- 125 (45%) → 45
- 51 (54) → 54 (for safety data without % symbol)
- 86 (91) → 91 (for safety data without % symbol)
**Safety Data Format**: In tables, extract the percentage value in parentheses, not the patient count outside parentheses
**ARM-SPECIFIC SAFETY**: Each arm must have its own unique safety data. Do NOT copy safety data from other arms.
"""

    field_list = "\n".join([f'"{field}": ""' for field in fields])
    
    tables_section = ""
    if tables_csv:
        tables_section = f"""
### TABLES FOR EXTRACTION ###
{tables_csv}
"""

    return f"""
SYSTEM: You are a precise clinical data extractor. Temperature 0. Never guess.

EXTRACT fields for ARM: {arm.get('arm_id', 'Unknown')} - {arm.get('generic_name', 'Unknown')} 
Patient count: {arm.get('number_of_patients', 'Unknown')}
NCT: {arm.get('nct_number', 'Unknown')}

CRITICAL: Only extract data specific to this arm. Do NOT mix data from other arms.
ARM ISOLATION: This arm must have its own unique data. Do NOT copy or use data from other treatment arms.
ARM-SPECIFIC EXTRACTION: Each arm has different efficacy and safety data. Extract ONLY data for this specific arm.

BACKBONE RULES FOR THIS ARM:
- Each arm should have unique ORR, CR, DCR and Safety parameters
- Cannot show values like (1, 2, 0) in one cell - This could mean there are multiple treatment arms
- There should be only one corresponding % value for each treatment
- PFS, OS, RFS, EFS, MFS values should be in Months (not percentage)
- If PFS or OS has "not reached" or "NR" mentioned put "NR" as the output
- If ORR is listed as "n (%) 7 (18)", extract "18" (the percentage in parentheses)
- If no value is found for efficacy parameters, leave the field empty ("")

If a field is not explicitly stated, output "".
Return JSON only with this EXACT structure:
{{
  "treatment_arms": [
    {{
{field_list}
    }}
  ]
}}

{safety_instructions}
{backbone_rules}

{tables_section}

PUBLICATION TEXT:
{publication_text[:55000]}
"""