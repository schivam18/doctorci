# src/prompts_pub.py
import json
from typing import List

def get_base_prompt() -> str:
    """Returns the foundational part of the prompt with general instructions."""
    return (
        "You are a world-class clinical expert specializing in data extraction for competitive intelligence. "
        "Your sole task is to analyze the provided text from a clinical trial publication and extract structured data. "
        "Adhere to the following critical instructions without deviation:\n\n"
        "**CRITICAL RULES:**\n"
        "1.  **JSON ONLY**: Your output MUST be a single raw JSON object, starting with `{` and ending with `}`. Do NOT include ```json or any other text. This is non-negotiable.\n"
        "2.  **DETECT ALL ARMS**: You must identify all distinct treatment arms in the text. An arm is a unique treatment regimen. Different dosages of the same drug are considered separate arms.\n"
        "3.  **EXTRACT ALL FIELDS**: For the shared fields and for each arm, you must extract all requested fields.\n"
        "4.  **NCT NUMBER IS PARAMOUNT**: You MUST find the 'NCT Number' (e.g., NCT01234567). It is the single most important field. If it is absolutely not present in the text, return an empty JSON object `{}`.\n"
        "5.  **NO HALLUCINATION**: Extract ONLY information present in the provided text. If a value is not mentioned for a field, use an empty string `\"\"`.\n"
    )

def generate_arm_aware_prompt(full_text: str) -> str:
    """
    Generates a simplified, focused prompt for raw data extraction.
    All validation and formatting will be handled by post-processing.
    """
    with open('data/keywords_structure_full_pub.json', 'r', encoding='utf-8') as f:
        keywords_structure = json.load(f)
    
    shared_fields = keywords_structure['shared_fields']
    arm_specific_fields = keywords_structure['arm_specific_fields']

    prompt = (
        "You are a clinical data extraction expert. Extract structured data from this clinical trial publication.\n\n"
        
        "**CRITICAL INSTRUCTIONS:**\n"
        "1. Return ONLY a raw JSON object (no markdown, no ```json, just the JSON)\n"
        "2. NCT Number is MANDATORY - if not found, return empty JSON {}\n"
        "3. Extract ONLY information present in the text - do not infer or guess\n"
        "4. Use empty string \"\" for missing values\n"
        "5. Identify ALL distinct treatment arms (different drugs, dosages, or combinations)\n"
        "6. Each arm gets ALL arm-specific fields with its own unique values\n\n"
        
        "**TREATMENT ARMS SPECIFICATION:**\n"
        "There should be one NCT unique identifier number for a treatment regimen and a publication. Regimen can be a single drug or a combination. Within one publication there can be one arm, two arms, three arms, or even more. Each arm is a separate treatment, whether its monotherapy or combination of two therapies or of three therapies. The ORR, CR or DCR and even all the Safety parameters should be unique to the treatment arm. For eg. NCT 123456789 has 3 treatment arms, first treatment is Drug A + Drug B, second one is Drug B + C, third one is Drug D. Each treatment whether single therapy or combination should have same NCT number within a trial, however can different response rates and safety analysis.\n"
        "If there are more than one publication for one NCT number, extract the data from the most recent one.\n"
        "For eg. if Pembro is a regimen in NCT 12121212 and Pembro is a regimen in NCT 54545454, then list both in separate rows with its unique NCT number.\n\n"
        
        "**FIELD-SPECIFIC EXTRACTION GUIDELINES:**\n\n"
        
        "**Publication name**: Should be listed in order like Name of Journal -Year-Volume-Pages. For eg. NEJM 2017; 377:1345-56. Journal is NEJM, Year is 2017, Volume is 377, Pages are 1345-1356. Name of the journal can be : Lancet, NEJM, JCO and similar.\n\n"
        
        "**NCT Number**: May be mentioned in different ways. For eg. \"This study is completed and was registered with ClinicalTrials.gov, number NCT01515189\" or \"This study was registered with ClinicalTrials.gov, number NCT01866319\", or \"Clinical trial information: NCT02085070\" or in a similar way within the publication. Extract NCT and every publication should have a NCT number, and no NCT is mentioned dont retrieve any information from that publication.\n\n"
        
        "**Generic Name**: Each Cell in generic name should be a treatment (whether its single, combo or triplet). If its a combo it should be explicitly shown both drugs with a + in middle. The same case for a triplet.\n\n"
        
        "**Stage**: 8 classes only.\n"
        "Stage I, Stage I/II, Stage II, Stage II/III, Stage III, Stage III/ Stage IV, Stage IV.\n\n"
        
        "**Trial name**: If there are multiple arms in one clinical trial, put each treatment in a different row and write the corresponding trial name.\n"
        "If there is only treatment arm use only Treatment arm 1 keywords. If more treatment arms in one publication use arm specific fields accordingly. There can also be same treatment regimen but different doses, for eg. Nivolumab has 3 different doses in the same publication, they should be interpreted as three separate arms. Another eg. One treatment is nivo and other ipilimumab then there should be two treatment arms. Each unique treatment arm should have the corresponding efficacy and safety.\n"
        "Trial name should be listed if it is a \"Keynote\", \"Checkmate\" or Masterkey\". For eg. Kyenote-006. If there is no associated link to these 3 names, then say \"No Name\".\n\n"
        
        "**Cancer type**: Should put only one of these to the associated generic name. 10 classes.\n"
        "Resected Cutaneous Melanoma, Unresectable Cutaneous Melanoma, Cutaneous melanoma with Brain metastasis, Cutaneous Melanoma with CNS metastasis, Uveal Melanoma, Mucosal Melanoma, Acral Melanoma, Basal Cell Carcinoma, Merkel Cell Carcinoma, Cutaneous Squamous Cell Carcinoma.\n\n"
        
        "**Line of therapy**: Should put only one of these to the associated generic name. 4 classes.\n"
        "Neoadjuvant, First Line or Untreated  or 2nd Line or 3rd Line+.\n"
        "Important note : 2nd line = include treatments when the 1st treatment failed, 3rd Line+ = include treatments who have failed the 2nd line treatment.\n\n"
        
        "**Efficacy and Safety**:\n"
        "There should be only one corresponding % value for each treatment (there shouldnt be more than 1 value in a cell) with all efficacy and safety sub-parameters like ORR, PFS, Grade 3+ Adverse events and more. In some abstracts, with one NCT number there are multiple arms within it, for eg. a monotherapy, and two combinations. These are part of one clinical trial but treatments are different. Each arm in a clinical trial should be an individual treatment.\n"
        "Capture individual efficacy and safety parameters for each treatment. Cannot show values like (1, 2, 0) in one cell - This could mean there are multiple treatment arms within the trial. Also there shouldn't be any text in the associated value of any of efficacy and safety parameters. Exception: Anywhere the PFS or OS has \"not reached\" or \"NR\" mentioned put \"NR\" as the output in that cell.\n"
        "If the ORR or other parameters are listed as \"n (%) 7 (18); 1 CR 11 (28); 2 CRs 0 (0)\". In that case the result should look like 18%, 28% and 0%, for the corresponding % values ( ).\n\n"
        
        "**Discontinuations**: If there is a statement like \"No treatment discontinuation occurred due to TEAE\", it means the Treatment discontinuation due to TEAE = 0.\n\n"
        
        "**PFS, OS, RFS, EFS, MFS**: values should be in Months (not percentage). For eg. Median PFS maybe listed as 12.0 (8.2–17.1) with 12 months being the actual value.\n\n"
        
        "**Total number of patients**: Each treatment should have a specific number of patients being tested in that arm. Dont combine all arms in one clinical trial and sum the patient numbers. We want patient numbers for each arm, corresponding to that particular generic name.\n\n"
        
        "**Research Sponsor**: 2 classes only.\n"
        "Every publication would have keyword such as \"Research sponsor\" or \"Sponsor\" or \"Funded by\" or \"Funding\".\n"
        "If the research sponsor is listed as \"None\" then, it will be given a tagname as \"non Industry-Sponsored\".\n"
        "If the research sponsor is listed as any name of a company or anything except \"none\", it will be given a tagname as \"Industry-Sponsored\".\n\n"
        
        "**p-value for PFS, OS, MFS, EFS, RFS**:\n"
        "Incase for p-value of any survival outcome, list the value corresponding to Non-significant, Significant or Highly Significant. For eg with p>0,05 it should be listed as \"Non-Significant\";  p-value between 0,05 to 0,001 or p<0,001, should be listed as \"Significant\"; p-value for 0,001 and beyond or p<0,0001 should be listed as \"Highly Significant\".\n\n"
        
        "**Type of therapy**: Based on this therapy it comes under.\n"
        "{\n"
        "  \"Immune Checkpoint Inhibitors\": {\n"
        "    \"approved\": [\"Pembrolizumab\", \"Nivolumab\", \"Ipilimumab\", \"Relatlimab\"],\n"
        "    \"unapproved\": [\"Triple checkpoint blockade\", \"new antibodies\"]\n"
        "  },\n"
        "  \"Cellular Therapy\": {\n"
        "    \"approved\": [\"Lifileucel\", \"Amtagvi\", \"TIL therapy\"],\n"
        "    \"unapproved\": [\"CAR T-cell therapy\"]\n"
        "  },\n"
        "  \"Targeted Therapy\": {\n"
        "    \"approved\": [\"Vemurafenib\", \"Dabrafenib\", \"Trametinib\", \"Encorafenib\"],\n"
        "    \"unapproved\": [\"Next-gen BRAF/MEK inhibitors\", \"new combos\"]\n"
        "  },\n"
        "  \"Oncolytic Virus Therapy\": {\n"
        "    \"approved\": [\"Talimogene laherparepvec\", \"Imlygic\"],\n"
        "    \"unapproved\": [\"Other viral vectors\"]\n"
        "  },\n"
        "  \"Chemotherapy\": {\n"
        "    \"approved\": [\"Dacarbazine\"],\n"
        "    \"unapproved\": [\"Temozolomide\", \"Fotemustine\"]\n"
        "  },\n"
        "  \"Bispecific Antibodies\": {\n"
        "    \"approved\": [\"Tebentafusp-tebn\", \"Kimmtrak\"],\n"
        "    \"unapproved\": [\"Other bispecifics in trial\"]\n"
        "  },\n"
        "  \"Vaccine/Immunostimulant\": {\n"
        "    \"approved\": [],\n"
        "    \"unapproved\": [\"Cancer vaccines\", \"immunostimulants\"]\n"
        "  }\n"
        "}\n\n"
        
        "**SPECIFIC KEYWORD FORMATTING INSTRUCTIONS:**\n\n"
        
        "**YES/NO Keywords**: For each of the following keywords, return only \"YES\" or \"NO\" based on whether it is explicitly mentioned or clearly implied in the full text. No other text is allowed.\n"
        "- Chemotherapy Naive\n"
        "- Chemotherapy Failed\n"
        "- Immune Checkpoint Inhibitor (ICI) Naive\n"
        "- Immune Checkpoint Inhibitor (ICI) failed\n"
        "- BRAF-mutation\n"
        "- NRAS-Mutation\n"
        "- Biomarker Inclusion\n"
        "- Trial run in Europe\n"
        "- Trial run in US\n"
        "- Trial run in China\n\n"
        
        "**Efficacy Keywords (Percentage)**: For the following keywords, extract the numeric value (percentage) only, without any \"%\" sign or text. If not found, leave the output blank.\n"
        "- Objective response rate (ORR)\n"
        "- Complete Response (CR)\n"
        "- Pathological Complete Response (pCR)\n"
        "- Complete Metabolic Response (CMR)\n"
        "- Disease Control Rate or DCR\n"
        "- Clinical Benefit Rate (CBR)\n"
        "- Duration of Response (DOR) rate\n"
        "- Progression free survival (PFS) rate at 6 months\n"
        "- Progression free survival (PFS) rate at 9 months\n"
        "- Progression free survival (PFS) rate at 12 months\n"
        "- Progression free survival (PFS) rate at 18 months\n"
        "- Progression free survival (PFS) rate at 24 months\n"
        "- Progression free survival (PFS) rate at 48 months\n"
        "- Overall survival (OS) rate at 6 months\n"
        "- Overall survival (OS) rate at 9 months\n"
        "- Overall survival (OS) rate at 12 months\n"
        "- Overall survival (OS) rate at 18 months\n"
        "- Overall survival (OS) rate at 24 months\n"
        "- Overall survival (OS) rate at 48 months\n\n"
        
        "**Efficacy Keywords (Numeric)**: Extract only the numeric values. No units, words, or percentage signs are allowed. If not found, leave blank.\n"
        "- Number of patients\n"
        "- Median Progression free survival (PFS)\n"
        "- Length of measuring PFS\n"
        "- p-value of PFS\n"
        "- Hazard ratio (HR) PFS\n"
        "- Median Overall survival (OS)\n"
        "- Length of measuring OS\n"
        "- p-value of OS\n"
        "- Hazard ratio (HR) OS\n"
        "- Event-Free Survival (EFS)\n"
        "- p-value of EFS\n"
        "- Hazard ratio (HR) EFS\n"
        "- Recurrence-Free Survival (RFS)\n"
        "- p-value of RFS\n"
        "- Length of measuring RFS\n"
        "- Hazard ratio (HR) RFS\n"
        "- Metastasis-Free Survival (MFS)\n"
        "- Length of measuring MFS\n"
        "- Hazard ratio (HR) MFS\n"
        "- Time to response (TTR)\n"
        "- Time to Progression (TTP)\n"
        "- Time to Next Treatment (TTNT)\n"
        "- Time to Treatment Failure (TTF)\n"
        "- Median Duration of response or DOR\n\n"
        
        "**Safety Keywords (Percentage)**: For each keyword below, extract only the numeric percentage values, without any % symbol or unit text. If not found, leave blank.\n"
        "- Adverse events (AE)\n"
        "- Treatment emergent adverse events (TEAE)\n"
        "- Treatment-related adverse events (TRAE)\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher adverse events (AE)\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment emergent adverse events (TEAE)\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-related adverse events (TRAE)\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 higher treatment-emergent adverse events (TEAE)\n"
        "- Grade 4 treatment emergent adverse events\n"
        "- Grade 5 treatment emergent adverse events\n"
        "- Immune related adverse events (irAEs)\n"
        "- Adverse events (AEs) leading to discontinuation\n"
        "- Treatment-emergent adverse events (TEAE) led to death\n"
        "- Adverse Events leading to death\n"
        "- Serious Adverse Events (SAE)\n"
        "- Serious treatment emergent adverse events\n"
        "- Serious treatment related adverse events\n"
        "- Cytokine Release Syndrome or CRS\n"
        "- White blood cell (WBC) decreased\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Immune related adverse events (irAEs)\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cytokine Release Syndrome or CRS\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thrombocytopenia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutropenia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Leukopenia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Nausea\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Anemia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Diarrhea\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Colitis\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hyperglycemia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Neutrophil count decreased\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Constipation\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Dyspnea\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Cough\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pyrexia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Bleeding\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pruritus\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Rash\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonia\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Thyroiditis\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hypophysitis\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Hepatitis\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Pneumonitis\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 Alanine aminotransferase\n"
        "- Grade ≥3 or Grade 3+ or Grade 3-5 or Grade 3-4 White blood cell (WBC) decreased\n\n"
        
        "**REQUIRED JSON STRUCTURE:**\n"
        "{\n"
        "  \"NCT Number\": \"NCT01234567\",\n"
        "  \"Publication name\": \"as written in text\",\n"
        "  \"Trial name\": \"as written in text\",\n"
        "  ... (ALL shared fields below),\n"
        "  \"treatment_arms\": [\n"
        "    {\n"
        "      \"Generic name\": \"Drug Name or Drug A + Drug B\",\n"
        "      \"Brand name\": \"Brand name if mentioned\",\n"
        "      \"Number of patients\": \"number for this arm only\",\n"
        "      \"Objective response rate (ORR)\": \"percentage value as written\",\n"
        "      ... (ALL arm-specific fields below)\n"
        "    },\n"
        "    {\n"
        "      \"Generic name\": \"Different Drug Name\",\n"
        "      \"Number of patients\": \"number for this arm only\",\n"
        "      ... (separate values for this arm)\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        
        "**SHARED FIELDS (same for all arms in this publication):**\n"
    )
    
    # Add shared fields
    for field in shared_fields:
        prompt += f"- {field}\n"
    
    prompt += "\n**ARM-SPECIFIC FIELDS (unique values per treatment arm):**\n"
    
    # Add arm-specific fields  
    for field in arm_specific_fields:
        prompt += f"- {field}\n"
    
    prompt += (
        "\n**EXTRACTION NOTES:**\n"
        "- Extract values exactly as they appear in the text.\n"
        "- For percentages, extract the full value (e.g., '45%' not just '45').\n"
        "- For missing data, use an empty string \"\".\n"
        "- **Key Sections**: Pay close attention to the 'Abstract', 'Patients', 'Methods', and 'Results' sections for the most reliable data.\n"
        "- **Safety Data**: Look in 'Adverse Events', 'Safety', or 'Toxicity' tables and text.\n"
        "- **Brand Names**: Look for trademarked drug names, often in parentheses.\n\n"
        
        "**PUBLICATION TEXT:**\n"
        f"{full_text}\n\n"
        
        "Return ONLY the JSON object with exact structure shown above."
    )
    
    return prompt 