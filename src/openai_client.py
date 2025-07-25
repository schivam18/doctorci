import json
import os
from typing import Any, Dict, List, Optional
import re

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

from src.logger_config import get_logger, log_performance
from enhanced_extractor import EnhancedClinicalExtractor

# Load environment variables
load_dotenv()


def calculate_cost(prompt_tokens, completion_tokens):
    """Calculate cost for gpt-4o-mini model"""
    # Rates per 1K tokens for 'gpt-4o-mini'
    rate_per_1k_prompt_tokens = 0.00015
    rate_per_1k_completion_tokens = 0.0006

    prompt_cost = (prompt_tokens / 1000) * rate_per_1k_prompt_tokens
    completion_cost = (completion_tokens / 1000) * rate_per_1k_completion_tokens
    total_cost = prompt_cost + completion_cost
    return total_cost


class OpenAIClient:
    """
    Enhanced OpenAI client with integrated clinical trial data extraction
    Uses the EnhancedClinicalExtractor for unified, high-quality extraction
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Enhanced OpenAIClient initialized")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.critical("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY is not set")
        
        self.client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        self.model = "gpt-4o-mini"
        self.max_tokens = 8000
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.request_count = 0
        
        # Initialize enhanced extractor
        self.enhanced_extractor = EnhancedClinicalExtractor()

    def get_chat_completion(self, messages, max_tokens=8000) -> str:
        """Get chat completion from OpenAI with cost tracking"""
        prompt_tokens = self.num_tokens_from_messages(messages)
        estimated_cost = calculate_cost(prompt_tokens, max_tokens)
        self.logger.info(f"Estimated cost for this request: ${estimated_cost:.6f}")

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.0,  # Set to 0.0 for maximum fact-based extraction
        )
        
        response_message = completion.choices[0].message.content
        usage = completion.usage
        actual_cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens)
        self.logger.info(f"Actual cost for this request: ${actual_cost:.6f}")

        self._update_totals(usage.prompt_tokens, usage.completion_tokens, actual_cost)
        return response_message

    @log_performance
    def extract_publication_data(self, full_text: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced extraction using the new EnhancedClinicalExtractor
        Integrates improved prompts, validation, and missing data protocols
        """
        self.logger.info("Starting enhanced extraction with improved prompts and validation")
        
        if not full_text:
            self.logger.error("Extraction skipped: The provided text is empty.")
            return None

        try:
            # Stage 1: Pre-validation using enhanced extractor
            can_process, validation_data = self.enhanced_extractor.pre_validate(full_text)
            if not can_process:
                self.logger.error(f"Pre-validation failed: {validation_data.get('errors', [])}")
                return None
            
            self.logger.info(f"Pre-validation passed: NCT={validation_data.get('nct_number')}, Arms={validation_data.get('treatment_arms_count', 0)}")

            # Stage 2: Create enhanced focused prompt
            focused_prompt = self.enhanced_extractor.create_focused_prompt(full_text, validation_data)
            self.logger.info(f"Enhanced prompt created: {len(focused_prompt):,} characters")

            # Stage 3: LLM Processing with enhanced prompt
            raw_response = self.get_chat_completion([{"role": "user", "content": focused_prompt}])
            if not raw_response:
                self.logger.error("LLM processing failed - no response received")
                return None

            # Stage 4: Parse response with robust JSON handling
            try:
                raw_json = json.loads(raw_response)
                self.logger.info("JSON parsing successful")
            except json.JSONDecodeError as e:
                # Use robust parser as fallback
                self.logger.warning(f"Initial JSON parsing failed: {e}. Attempting robust parsing...")
                raw_json = self._robust_parse_json(raw_response)
                if not raw_json:
                    self.logger.error(f"JSON parsing failed even with robust parser: {e}")
                    return None
                self.logger.info("Robust JSON parsing successful")

            # Stage 5: Enhanced validation and cleaning
            validated_data = self.enhanced_extractor.validate_and_clean_data(raw_json, validation_data)
            
            if "data" in validated_data and validated_data["data"]:
                extracted_data = validated_data["data"]
                treatment_arms_count = len(extracted_data.get('treatment_arms', []))
                
                # Log validation results
                metadata = validated_data.get("extraction_metadata", {})
                error_count = len(metadata.get("errors", []))
                warning_count = len(metadata.get("warnings", []))
                
                self.logger.info(f"Enhanced extraction successful:")
                self.logger.info(f"  - Treatment arms: {treatment_arms_count}")
                self.logger.info(f"  - Validation status: {metadata.get('validation_status', 'unknown')}")
                self.logger.info(f"  - Errors: {error_count}, Warnings: {warning_count}")
                
                if error_count > 0:
                    self.logger.warning(f"Validation errors found: {metadata.get('errors', [])}")
                
                return extracted_data
            else:
                self.logger.error("Enhanced extraction failed: No valid data returned")
                return None
                
        except Exception as e:
            self.logger.error(f"Enhanced extraction error: {e}", exc_info=True)
            return None

    def num_tokens_from_messages(self, messages):
        """Calculate token count for messages"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("o200k_base")
        
        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    def _update_totals(self, prompt_tokens: int, completion_tokens: int, cost: float):
        """Update running totals for usage tracking"""
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += cost
        self.request_count += 1

    def _robust_parse_json(self, json_string: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced robust JSON parser that attempts to fix common LLM errors
        Handles markdown fences, trailing commas, and incomplete JSON objects
        """
        original_string = json_string  # Keep for debugging
        
        # 1. Strip markdown fences and whitespace
        json_string = json_string.strip()
        if json_string.startswith("```"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        json_string = json_string.strip()

        # 2. Find the start and end of the main JSON object
        try:
            start_index = json_string.index('{')
            end_index = json_string.rindex('}') + 1
            json_string = json_string[start_index:end_index]
        except ValueError:
            self.logger.error("Could not find a valid JSON object within the response string.")
            return None

        # 3. Fix trailing commas in objects and arrays
        json_string = re.sub(r",\s*([\}\]])", r"\1", json_string)

        # 4. Attempt to parse the cleaned string
        try:
            parsed = json.loads(json_string)
            # Check if this has the required structure for clinical trials
            if "treatment_arms" in parsed or "NCT Number" in parsed:
                return parsed
            else:
                self.logger.warning("Parsed JSON is missing expected clinical trial structure. Attempting recovery.")
        except json.JSONDecodeError as e:
            self.logger.warning(f"Initial JSON parsing failed: {e}. Attempting to find largest valid JSON object.")

        # Enhanced fallback: try to find the complete JSON object with clinical trial data
        try:
            # Look for patterns that indicate clinical trial data
            clinical_patterns = [
                r'"treatment_arms"\s*:\s*\[',
                r'"NCT Number"\s*:\s*"',
                r'"Clinical Trial Phase"\s*:\s*"'
            ]
            
            has_clinical_data = any(re.search(pattern, json_string) for pattern in clinical_patterns)
            
            if has_clinical_data:
                self.logger.info("Found clinical trial patterns in JSON string. Attempting targeted recovery.")
                
                # Try to find the JSON object that contains clinical trial data
                start_pos = json_string.find('{')
                if start_pos != -1:
                    # Find the matching closing brace by counting braces
                    brace_count = 0
                    for i in range(start_pos, len(json_string)):
                        if json_string[i] == '{':
                            brace_count += 1
                        elif json_string[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                candidate = json_string[start_pos:i+1]
                                try:
                                    parsed = json.loads(candidate)
                                    if any(key in parsed for key in ["treatment_arms", "NCT Number", "Clinical Trial Phase"]):
                                        self.logger.info("Successfully recovered complete JSON with clinical trial data.")
                                        return parsed
                                except json.JSONDecodeError:
                                    continue
            
            # Original fallback logic if targeted recovery fails
            best_match = None
            best_match_has_clinical_data = False
            
            # Find all possible JSON objects (stuff between balanced {})
            open_braces = [i for i, char in enumerate(json_string) if char == '{']
            close_braces = [i for i, char in enumerate(json_string) if char == '}']
            
            for start in open_braces:
                for end in close_braces:
                    if start < end:
                        substring = json_string[start:end+1]
                        try:
                            # Test if this substring is valid JSON
                            parsed = json.loads(substring)
                            has_clinical_data = any(key in parsed for key in ["treatment_arms", "NCT Number", "Clinical Trial Phase"])
                            
                            # Prioritize JSON objects that have clinical trial data
                            if has_clinical_data and not best_match_has_clinical_data:
                                best_match = substring
                                best_match_has_clinical_data = True
                            elif (not best_match_has_clinical_data and 
                                  (best_match is None or len(substring) > len(best_match))):
                                best_match = substring
                                
                        except json.JSONDecodeError:
                            continue
            
            if best_match:
                self.logger.info(f"Successfully recovered a valid JSON object. Has clinical data: {best_match_has_clinical_data}")
                parsed = json.loads(best_match)
                
                # Debug logging for problematic cases
                if not best_match_has_clinical_data:
                    self.logger.warning(f"Recovered JSON missing clinical trial data. Keys found: {list(parsed.keys())}")
                    self.logger.debug(f"Original response length: {len(original_string)}")
                    self.logger.debug(f"Cleaned JSON length: {len(json_string)}")
                    self.logger.debug(f"Recovered JSON length: {len(best_match)}")
                    
                return parsed

        except Exception as fallback_e:
            self.logger.error(f"Fallback JSON parsing also failed: {fallback_e}")

        self.logger.error(f"Final JSON parsing attempt failed after all fallbacks.")
        self.logger.debug(f"Problematic JSON string after cleaning: {json_string[:500]}...")
        return None

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        return {
            "total_requests": self.request_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": self.total_cost,
            "model_used": self.model,
            "extraction_method": "enhanced_clinical_extractor"
        }

    def print_usage_summary(self):
        """Print detailed usage summary"""
        summary = self.get_usage_summary()
        print("\n" + "=" * 60)
        print("ENHANCED OPENAI API USAGE SUMMARY")
        print("=" * 60)
        print(f"Model: {summary['model_used']}")
        print(f"Extraction Method: {summary['extraction_method']}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Prompt Tokens: {summary['total_prompt_tokens']:,}")
        print(f"Total Completion Tokens: {summary['total_completion_tokens']:,}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.6f}")
        print("=" * 60)

    def extract_batch_publications(self, publications: List[str]) -> List[Dict[str, Any]]:
        """
        Extract data from multiple publications using enhanced pipeline
        """
        results = []
        
        for i, pub_text in enumerate(publications):
            self.logger.info(f"Processing publication {i+1}/{len(publications)}")
            
            result = self.extract_publication_data(pub_text)
            if result:
                result["batch_index"] = i
                results.append(result)
            else:
                self.logger.warning(f"Failed to extract data from publication {i+1}")
        
        return results

    def validate_extraction_quality(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extraction quality and provide quality metrics
        """
        if not extracted_data:
            return {"quality_score": 0, "issues": ["No data extracted"]}
        
        quality_metrics = {
            "quality_score": 0,
            "completeness": 0,
            "issues": [],
            "warnings": []
        }
        
        # Check for required fields
        required_fields = ["NCT Number", "treatment_arms"]
        missing_required = [field for field in required_fields if not extracted_data.get(field)]
        
        if missing_required:
            quality_metrics["issues"].extend([f"Missing required field: {field}" for field in missing_required])
        
        # Check treatment arms quality
        treatment_arms = extracted_data.get("treatment_arms", [])
        if treatment_arms:
            arm_quality = []
            for i, arm in enumerate(treatment_arms):
                arm_completeness = 0
                arm_fields = ["Generic name", "Number of patients", "Line of Treatment"]
                for field in arm_fields:
                    if arm.get(field):
                        arm_completeness += 1
                arm_quality.append(arm_completeness / len(arm_fields))
            
            quality_metrics["completeness"] = sum(arm_quality) / len(arm_quality) if arm_quality else 0
        
        # Calculate overall quality score
        base_score = 50 if extracted_data.get("NCT Number") else 0
        completeness_score = quality_metrics["completeness"] * 30
        issue_penalty = len(quality_metrics["issues"]) * 5
        
        quality_metrics["quality_score"] = max(0, min(100, base_score + completeness_score - issue_penalty))
        
        return quality_metrics
