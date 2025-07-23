import json
import re

def load_keywords_structure():
    """Load the keywords structure from the JSON file."""
    with open('data/keywords_structure.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_field_name(field_name):
    """Clean field names by fixing character encoding issues."""
    # Replace common encoding issues
    field_name = field_name.replace('â‰¥', '≥')
    field_name = field_name.replace('â€™', "'")
    field_name = field_name.replace('â€œ', '"')
    field_name = field_name.replace('â€', '"')
    return field_name

def validate_p_value_classification(p_value_text):
    """
    Helper function to classify p-values based on the specified criteria.
    This can be used for additional validation or conversion if needed.
    """
    if not p_value_text or p_value_text.strip() == "":
        return ""
    
    # Extract numeric p-value if possible
    p_match = re.search(r'p[<>=]\s*(\d*\.?\d+)', p_value_text.lower())
    
    if p_match:
        p_val = float(p_match.group(1))
        if p_val > 0.05:
            return "Non-Significant"
        elif p_val <= 0.05 and p_val > 0.001:
            return "Significant"
        elif p_val <= 0.001:
            return "Highly Significant"
    
    # If we can't extract numeric value, look for keywords
    if any(keyword in p_value_text.lower() for keyword in ['non-significant', 'not significant', 'ns']):
        return "Non-Significant"
    elif any(keyword in p_value_text.lower() for keyword in ['highly significant', 'very significant']):
        return "Highly Significant"
    elif any(keyword in p_value_text.lower() for keyword in ['significant', 'sig']):
        return "Significant"
    
    return p_value_text  # Return original if can't classify

def extract_and_process_trial_data(abstract_text):
    """Complete pipeline to extract and process trial data."""
    
    # Load keywords structure for abstract processing
    keywords = load_keywords_structure()
    all_columns = []
    for category, fields in keywords.items():
        cleaned_fields = [clean_field_name(field) for field in fields]
        all_columns.extend(cleaned_fields)
    
    # Generate extraction prompt
    prompt = (
        "You are a clinical expert in competitive intelligence. Your task is to analyze the following clinical trial abstract "
        "and extract structured data according to these critical requirements:\n\n"
        
        "**IMPORTANT: Return ONLY raw JSON without any markdown formatting or code blocks.**\n"
        "Do not include ```json or ``` markers. The response should start with { and end with }.\n\n"
        
        "**NCT NUMBER EXTRACTION - CRITICAL REQUIREMENT**:\n"
        "NCT numbers are commonly found after 'ClinicalTrials.gov' or 'Clinical trial information'. "
        "Look for patterns like:\n"
        "- 'This study is completed and was registered with ClinicalTrials.gov, number NCT01515189'\n"
        "- 'This study was registered with ClinicalTrials.gov, number NCT01866319'\n"
        "- 'Clinical trial information: NCT02085070'\n"
        "- Similar variations within the publication\n\n"
        
        "**MANDATORY**: Extract the NCT number and every publication MUST have an NCT number. "
        "If no NCT number is mentioned, do not retrieve any information from that publication.\n\n"
        
        "**TREATMENT ARMS WITHIN NCT**:\n"
        "There should be one NCT unique identifier number for a treatment. Within one NCT number there can be one arm, "
        "two arms, three arms, or even more. Each arm is a separate treatment, whether its monotherapy or combination "
        "of two therapies or of three therapies. The ORR, CR or DCR and even all the Safety parameters should be unique "
        "to the treatment arm. For eg. NCT 123456789 has 3 treatment arms, first treatment is Drug A + Drug B, second "
        "one is Drug B + C, third one is Drug D. Each treatment whether single therapy or combination should have same "
        "NCT number within a trial, however can different response rates and safety analysis.\n\n"
        
        "The NCT number of the abstract is located in the 'Clinical trial information' section of each abstract. "
        "Don't use NCT number listed in the Background or Introduction.\n\n"
        
        "If there is only treatment arm use only A43:112. If more treatment arms in one NCT use accordingly. "
        "There can also be same treatment regimen but different doses, for eg. NCT01968109, in which Nivo has same "
        "dose but RELA dose changes. Make individual row for each unique treatment doses and list corresponding "
        "efficacy and safety.\n\n"
        
        "**GENERIC NAME**:\n"
        "Each Cell in generic name should be a treatment (whether its single, combo or triplet). If its a combo it "
        "should be explicitely shown both drugs with a + in middle. The same case for a triplet.\n\n"
        
        "**STAGE**: 8 classes only\n"
        "Stage I, Stage I/II, Stage II, Stage II/III, Stage III, Stage III/IV, Stage IV.\n\n"
        
        "**TRIAL NAME**:\n"
        "If there are multiple arms in one clinical trial, put each treatment in a different row and write the "
        "corresponding trial name. For eg. in one trial KEYMAKERU02A there are 3 arms -- Pembro + Qmab + Vibo, "
        "Pembro + Qmab + Len, Pembro + ATRA. Each combo or triplet is a treatment and the corresponding KEYMAKER2A "
        "trial should be listed for each treatment.\n\n"
        
        "**CANCER TYPE**:\n"
        "Should put only one of these to the associated generic name. 7 classes:\n"
        "Resected Cutaneous Melanoma, Unresectable Cutaneous Melanoma, Cutaneous melanoma with Brain metastasis, "
        "Cutaneous Melanoma with CNS metastasis, Uveal Melanoma, Mucosal Melanoma, Acral Melanoma, Basal Cell Carcinoma, "
        "Merkel Cell Carcinoma, Cutaneous Squamous Cell Carcinoma.\n\n"
        
        "**LINE OF THERAPY**:\n"
        "Should put only one of these to the associated generic name. 3 classes:\n"
        "Neoadjuvant, First Line or Untreated, 2nd Line and beyond (include treatments when the 1st treatment failed).\n\n"
        
        "**EFFICACY AND SAFETY**:\n"
        "There should be only one corresponding % value for each treatment (there shouldn't be more than 1 value in a cell) "
        "with all efficacy and safety sub-parameters like ORR, PFS, Grade 3+ Adverse events and more. In some abstracts, "
        "with one NCT number there are multiple arms within it, for eg. a monotherapy, and two combinations. These are "
        "part of one clinical trial but treatments are different. Each arm in a clinical trial should be an individual treatment.\n\n"
        
        "Capture individual efficacy and safety parameters for each treatment. Cannot show values like (1, 2, 0) in one cell - "
        "This could mean there are multiple treatment arms within the trial. Also there shouldn't be any text in the associated "
        "value of any of efficacy and safety parameters. Exception: Anywhere the PFS or OS has 'not reached' or 'NR' mentioned "
        "put 'NR' as the output in that cell.\n\n"
        
        "If the ORR or other parameters are listed as ' n (%) 7 (18); 1 CR 11 (28); 2 CRs 0 (0)'. In that case the result "
        "should look like 18%, 28% and 0%, for the corresponding % values ( ).\n\n"
        
        "PFS, OS, RFS, EFS, MFS, values should be in Months (not percentage). For eg. Median PFS maybe listed as 12.0 (8.2–17.1). "
        "Within the () is the range.\n\n"
        
        "**TOTAL NUMBER OF PATIENTS**:\n"
        "Each treatment should have a specific number of patients being tested in that arm. Don't combine all arms in one "
        "clinical trial and sum the patient numbers. We want patient numbers for each arm, corresponding to that particular generic name.\n\n"
        
        "**RESEARCH SPONSOR**: 2 classes only\n"
        "If the research sponsor is listed as 'None' then, it will be given a tagname as 'Non Industry-Sponsored'.\n"
        "If the research sponsor is listed as any name of a company or anything except 'none', it will be given a tagname as 'Industry-Sponsored'.\n"
        "Every abstract has a Research sponsor at the end.\n\n"
        
        "**P-VALUE FOR PFS, OS, MFS, EFS, RFS**:\n"
        "Incase for p-value of any survival outcome, list the value corresponding to Non-significant, Significant or Highly Significant. "
        "For eg. with p>0,05 it should be listed as 'Non-Significant'; p-value between 0,05 to 0,001 or p<0,001, should be listed as 'Significant'; "
        "p-value for 0,001 and beyond or p<0,0001 should be listed as 'Highly Significant'.\n\n"
        
        "**ABSTRACT PRIORITIZATION RULE**:\n"
        "If more than one abstract is found for one NCT number, extract the data from the most recent abstract, that is 2025 ASCO file.\n\n"
        
        "**CRITICAL DATA FORMATTING RULES FOR EXCEL COMPATIBILITY**:\n"
        "- For percentage fields: Extract ONLY the numeric value without % symbol (e.g., '18' not '18%')\n"
        "- For number-only fields: Extract ONLY the numeric value (e.g., '25.5' not '25.5%')\n"
        "- Extract percentages from formats like 'n (%) 7 (18)' → enter '18' (numeric only)\n"
        "- For 'not reached' or 'NR' values → enter 'NR' as text\n"
        "- For empty/missing values → leave as empty string ''\n"
        "- NO text descriptions in numerical fields\n"
        "- NO combined values like '(1, 2, 0)' in single cells\n"
        "- Each treatment arm must have individual patient counts\n"
        "- For confidence intervals like '95% CI: 12.5-18.7', extract the main value before CI\n\n"
        
        "**OUTPUT FORMAT**: Extract data for TWO separate Excel files:\n"
        "- `industry_sponsored_trials.xlsx` - Contains trials where Research Sponsor is NOT 'None'\n"
        "- `non_industry_sponsored_trials.xlsx` - Contains trials where Research Sponsor is 'None'\n\n"
    )

    # Add all required fields with proper encoding
    prompt += "**REQUIRED COLUMNS** (all must be included for each treatment arm):\n"
    for i, field in enumerate(all_columns, 1):
        prompt += f"{i}. {field}\n"

    prompt += (
        "\n**REQUIRED JSON OUTPUT FORMAT** (return ONLY the raw JSON, no markdown):\n"
        "{\n"
        '  "sponsor_type": "Industry-Sponsored" or "Non Industry-Sponsored",\n'
        '  "treatment_arms": [\n'
        '    {\n'
    )

    # Add all columns to the JSON structure
    for i, col in enumerate(all_columns):
        if i > 0:
            prompt += ',\n'
        prompt += f'      "{col}": "string value"'

    prompt += (
        '\n    }\n'
        '  ]\n'
        "}\n\n"
        "**CRITICAL REQUIREMENTS**:\n"
        "1. **NCT NUMBER IS MANDATORY**: Must extract NCT number from patterns like 'ClinicalTrials.gov, number NCT01515189' or 'Clinical trial information: NCT02085070'. If no NCT found, return empty response.\n"
        "2. Each treatment arm = separate object in 'treatment_arms' array\n"
        "3. All columns must be present for each treatment arm (use empty string if not available)\n"
        "4. Follow exact formatting rules for each field type - NO % symbols in numeric fields\n"
        "5. Extract ONLY numeric values for percentage fields (Excel will format them)\n"
        "6. Classify sponsor type correctly for file separation\n"
        "7. Use controlled categories exactly as specified\n"
        "8. For p-values of survival outcomes, use the three-tier classification system\n"
        "9. Prioritize most recent abstracts (2025 ASCO file) when multiple abstracts exist for same NCT\n"
        "10. Return ONLY raw JSON without any markdown formatting or code blocks\n"
        "11. Remember: Grade ≥3 means Grade 3 or higher adverse events\n"
        "12. Each treatment arm must have individual efficacy and safety parameters\n"
        "13. Use '+' to separate drugs in combination therapies\n"
        "14. Extract NCT numbers only from 'Clinical trial information' section, not from Background/Introduction\n"
        "15. For survival values, extract in months, not percentages\n"
        "16. For p-values, use Non-Significant/Significant/Highly Significant classification\n\n"
        "**Abstract to Process:**\n\n"
        f"{abstract_text}\n"
    )

    return prompt