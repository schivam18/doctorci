import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging
from src.logger_config import get_logger, log_performance
import json

# Load environment variables
load_dotenv()

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

def generate_qc_prompt(publication_text):
    prompt = (
        "You are a clinical expert in competitive intelligence. Extract ONLY the following 11 critical QC fields from the clinical trial publication. "
        "Return ONLY raw JSON, no markdown or code blocks. The response should start with { and end with }.\n\n"
        "**QC FIELDS TO EXTRACT:**\n"
    )
    for i, field in enumerate(QC_KEYWORDS, 1):
        prompt += f"{i}. {field}\n"
    prompt += ("\n**FIELD FORMATTING RULES:**\n"
        "- NCT Number: Must match pattern NCT########.\n"
        "- Generic name: Should be a drug or combo (e.g., Nivolumab + Ipilimumab).\n"
        "- Cancer Type: Must match one of 10 defined melanoma types.\n"
        "- Line of Treatment: Must be one of: Neoadjuvant, First Line, 2nd Line, 3rd Line+.\n"
        "- Number of patients: Numeric only.\n"
        "- ORR: Single numeric percent (e.g., 42).\n"
        "- PFS/OS: Numeric (months) or 'NR'.\n"
        "- Adverse events (AE): Single percent.\n"
        "- Grade ≥3 adverse events (AE): Single percent.\n"
        "- TEAE discontinuation: Percent or 0 if no discontinuation.\n"
        "\n**REQUIRED JSON OUTPUT FORMAT:**\n"
        "{\n  'qc_fields': {\n"
    )
    for i, field in enumerate(QC_KEYWORDS):
        comma = ',' if i < len(QC_KEYWORDS) - 1 else ''
        prompt += f"    '{field}': 'value'{comma}\n"
    prompt += "  }\n}\n\n"
    prompt += "Publication to Process:\n\n" + publication_text
    return prompt

class QCOpenAIClient:
    def __init__(self):
        self.logger = get_logger(__name__)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.critical("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        self.model = 'gpt-4o-mini'
        self.max_tokens = 2000

    @log_performance
    def extract_qc_fields(self, publication_text):
        prompt = generate_qc_prompt(publication_text)
        self.logger.info(f"Extracting QC fields from publication (length: {len(publication_text)} chars)")
        try:
            messages = [{"role": "user", "content": prompt}]
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.1
            )
            content = completion.choices[0].message.content
            self.logger.debug(f"Raw LLM output: {content}")
            qc_data = json.loads(content)
            self.logger.info("QC extraction successful.")
            return qc_data
        except Exception as e:
            self.logger.error(f"QC extraction failed: {str(e)}", exc_info=True)
            raise 