# openai_client.py

import json
import os
from typing import Any, Dict, List, Optional
import asyncio
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

from src.logger_config import get_logger, log_performance
from src.prompts_pub import generate_arm_aware_prompt
from src.post_processor import process_extracted_data
from src.enhanced_extractor import EnhancedClinicalExtractor
from src.chunk_templates import CHUNK_FIELD_MAP

# Load environment variables
load_dotenv()

# KEYWORDS_STRUCTURE is no longer needed here, it's handled by the prompt generator.

def calculate_cost(prompt_tokens, completion_tokens):
    # Rates per 1K tokens for 'gpt-4o-mini'
    rate_per_1k_prompt_tokens = 0.00015
    rate_per_1k_completion_tokens = 0.0006

    prompt_cost = (prompt_tokens / 1000) * rate_per_1k_prompt_tokens
    completion_cost = (completion_tokens / 1000) * rate_per_1k_completion_tokens
    total_cost = prompt_cost + completion_cost
    return total_cost


class OpenAIClient:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("OpenAIClient initialized")
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

    def get_chat_completion(self, messages, max_tokens=8000) -> str:
        prompt_tokens = self.num_tokens_from_messages(messages)
        estimated_cost = calculate_cost(prompt_tokens, max_tokens)
        self.logger.info(f"Estimated cost for this request: ${estimated_cost:.6f}")

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.0, # Set to 0.0 for maximum fact-based extraction
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
        Runs a single, comprehensive extraction process on the full text of a document,
        expecting a nested JSON with document and treatment arm data.
        """
        self.logger.info("Starting arm-aware extraction from full paper text.")
        
        if not full_text:
            self.logger.error("Extraction skipped: The provided text is empty.")
            return None

        prompt = generate_arm_aware_prompt(full_text)
        
        try:
            response_content = self.get_chat_completion([{"role": "user", "content": prompt}])
            parsed_data = self._parse_json_response(response_content)
            if parsed_data and "treatment_arms" in parsed_data:
                # Apply comprehensive post-processing (includes all validation and formatting)
                processed_data = process_extracted_data(parsed_data, full_text)
                self.logger.info(f"Extraction successful. Found {len(processed_data['treatment_arms'])} treatment arms.")
                return processed_data
            else:
                self.logger.error("Extraction failed: The returned JSON is missing the 'treatment_arms' key or is invalid.")
                return None
        except Exception as e:
            self.logger.error(f"An error occurred during extraction: {e}", exc_info=True)
            return None

    @log_performance
    def extract_full_publication_chunked(self, full_text: str) -> Optional[Dict[str, Any]]:
        """
        Run chunked extraction process on full publication text
        """
        self.logger.info("Starting chunked extraction pipeline")
        
        if not full_text:
            self.logger.error("Empty text provided")
            return None
        
        extractor = EnhancedClinicalExtractor()
        
        try:
            # Stage 1: Discover treatment arms
            self.logger.info("Stage 1: Discovering treatment arms")
            arm_discovery_prompt = extractor.detect_arms(full_text)["prompt"]
            
            arms_response = self.get_chat_completion([{
                "role": "user", 
                "content": arm_discovery_prompt
            }], max_tokens=1000)
            
            arms_data = self._parse_json_response(arms_response)
            if not arms_data or "treatment_arms" not in arms_data:
                self.logger.error("Failed to discover treatment arms")
                return None
            
            arms = arms_data["treatment_arms"]
            self.logger.info(f"Discovered {len(arms)} treatment arms")
            
            # Stage 2: Extract shared data (chunks 1 and 9)
            self.logger.info("Stage 2: Extracting shared publication data")
            shared_data = {}
            
            for chunk_id in [1, 9]:
                prompt = extractor.build_chunk_prompt(full_text, None, chunk_id)
                response = self.get_chat_completion([{
                    "role": "user",
                    "content": prompt["prompt"]
                }])
                
                chunk_data = self._parse_json_response(response)
                if chunk_data:
                    shared_data.update(chunk_data)
                    self.logger.info(f"Extracted shared chunk {chunk_id}")
            
            # Stage 3: Extract arm-specific data (chunks 2-8 per arm)
            self.logger.info("Stage 3: Extracting arm-specific data")
            final_arms = []
            
            for arm in arms:
                self.logger.info(f"Processing arm: {arm.get('arm_id')} - {arm.get('generic_name')}")
                
                arm_partials = []
                
                # Process chunks 2-8 for this arm
                for chunk_id in [2, 3, 4, 5, 6, 7, 8]:
                    prompt = extractor.build_chunk_prompt(full_text, arm, chunk_id)
                    response = self.get_chat_completion([{
                        "role": "user",
                        "content": prompt["prompt"]
                    }])
                    
                    chunk_data = self._parse_json_response(response)
                    if chunk_data:
                        arm_partials.append(chunk_data)
                        self.logger.info(f"Extracted arm {arm['arm_id']} chunk {chunk_id}")
                
                # Merge this arm's data
                merged_arm = extractor.merge_chunk_results(
                    arm["arm_id"], 
                    shared_data.copy(), 
                    arm_partials
                )
                
                # Add arm identification data
                merged_arm.update({
                    "Generic name": arm.get("generic_name", ""),
                    "Number of patients": arm.get("number_of_patients", ""),
                    "Dosage": arm.get("dose", "")
                })
                
                final_arms.append(merged_arm)
            
            # Stage 4: Compile final result
            final_result = {
                **shared_data,
                "treatment_arms": final_arms,
                "extraction_metadata": {
                    "approach": "chunked",
                    "arms_discovered": len(arms),
                    "arms_processed": len(final_arms),
                    "total_llm_calls": self.request_count,
                    "total_cost": self.total_cost,
                    "extraction_date": extractor._get_current_datetime()
                }
            }
            
            self.logger.info(f"Chunked extraction completed: {len(final_arms)} arms processed")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Chunked extraction failed: {e}", exc_info=True)
            return None

    @log_performance
    def extract_full_publication_comprehensive(self, full_text: str) -> Optional[Dict[str, Any]]:
        """
        Run comprehensive chunked extraction process with all new fields
        """
        self.logger.info("Starting comprehensive chunked extraction pipeline")
        
        if not full_text:
            self.logger.error("Empty text provided")
            return None
        
        extractor = EnhancedClinicalExtractor()
        
        try:
            # Stage 1: Discover treatment arms
            self.logger.info("Stage 1: Discovering treatment arms")
            arm_discovery_prompt = extractor.detect_arms(full_text)["prompt"]
            
            arms_response = self.get_chat_completion([{
                "role": "user", 
                "content": arm_discovery_prompt
            }], max_tokens=1000)
            
            arms_data = self._parse_json_response(arms_response)
            if not arms_data or "treatment_arms" not in arms_data:
                self.logger.error("Failed to discover treatment arms")
                return None
            
            arms = arms_data["treatment_arms"]
            self.logger.info(f"Discovered {len(arms)} treatment arms")
            
            # Stage 2: Extract shared data (chunks 1 and 10)
            self.logger.info("Stage 2: Extracting shared publication data")
            shared_data = {}
            
            for chunk_id in [1, 10]:
                prompt = extractor.build_chunk_prompt(full_text, None, chunk_id)
                response = self.get_chat_completion([{
                    "role": "user",
                    "content": prompt["prompt"]
                }])
                
                chunk_data = self._parse_json_response(response)
                if chunk_data:
                    # Extract data from treatment_arms wrapper if present
                    if "treatment_arms" in chunk_data and chunk_data["treatment_arms"]:
                        # Take the first arm's data (should be the only one)
                        extracted_data = chunk_data["treatment_arms"][0]
                    else:
                        # No wrapper, use data directly
                        extracted_data = chunk_data
                    
                    shared_data.update(extracted_data)
                    self.logger.info(f"Extracted shared chunk {chunk_id}")
            
            # Stage 3: Extract arm-specific data (chunks 2-9 per arm)
            self.logger.info("Stage 3: Extracting comprehensive arm-specific data")
            final_arms = []
            
            for arm in arms:
                self.logger.info(f"Processing arm: {arm.get('arm_id')} - {arm.get('generic_name')}")
                
                arm_partials = []
                
                # Process chunks 2-9 for this arm
                for chunk_id in [2, 3, 4, 5, 6, 7, 8, 9]:
                    prompt = extractor.build_chunk_prompt(full_text, arm, chunk_id)
                    response = self.get_chat_completion([{
                        "role": "user",
                        "content": prompt["prompt"]
                    }])
                    
                    chunk_data = self._parse_json_response(response)
                    if chunk_data:
                        # Extract data from treatment_arms wrapper if present
                        if "treatment_arms" in chunk_data and chunk_data["treatment_arms"]:
                            # Take the first arm's data (should be the only one)
                            extracted_data = chunk_data["treatment_arms"][0]
                        else:
                            # No wrapper, use data directly
                            extracted_data = chunk_data
                        
                        arm_partials.append(extracted_data)
                        self.logger.info(f"Extracted arm {arm['arm_id']} chunk {chunk_id}")
                
                # Merge this arm's data
                merged_arm = extractor.merge_chunk_results(
                    arm["arm_id"], 
                    shared_data.copy(), 
                    arm_partials
                )
                
                # Add arm identification data
                merged_arm.update({
                    "Generic name": arm.get("generic_name", ""),
                    "Number of patients": arm.get("number_of_patients", ""),
                    "Dosage": arm.get("dose", "")
                })
                
                final_arms.append(merged_arm)
            
            # Stage 4: Compile final result
            total_fields = sum(len(fields) for fields in CHUNK_FIELD_MAP.values() if fields)
            
            final_result = {
                **shared_data,
                "treatment_arms": final_arms,
                "extraction_metadata": {
                    "approach": "comprehensive_chunked",
                    "arms_discovered": len(arms),
                    "arms_processed": len(final_arms),
                    "total_llm_calls": self.request_count,
                    "total_cost": self.total_cost,
                    "total_fields_available": total_fields,
                    "extraction_date": datetime.now().isoformat()
                }
            }
            
            self.logger.info(f"Comprehensive extraction completed: {len(final_arms)} arms processed")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Comprehensive extraction failed: {e}", exc_info=True)
            return None

    def num_tokens_from_messages(self, messages):
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
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += cost
        self.request_count += 1

    def _robust_parse_json(self, json_string: str) -> Optional[Dict[str, Any]]:
        """
        A more robust JSON parser that attempts to fix common errors from LLMs.
        - Removes markdown code fences.
        - Attempts to find the main JSON object even with leading/trailing text.
        - Fixes trailing commas.
        """
        original_string = json_string  # Keep for debugging
        
        # 1. Strip markdown fences and whitespace
        json_string = json_string.strip()
        if json_string.startswith("```json"):
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
        # This is a common LLM error.
        import re
        json_string = re.sub(r",\s*([\}\]])", r"\1", json_string)

        # 4. Attempt to parse the cleaned string
        try:
            parsed = json.loads(json_string)
            # Check if this has the required structure
            if "treatment_arms" in parsed:
                return parsed
            else:
                self.logger.warning("Parsed JSON is missing 'treatment_arms' key. Attempting recovery.")
                # Continue to fallback logic
        except json.JSONDecodeError as e:
            self.logger.warning(f"Initial JSON parsing failed: {e}. Attempting to find largest valid JSON object.")

        # Enhanced fallback: try to find the complete JSON object
        try:
            # Look for patterns that might indicate a complete JSON with treatment_arms
            treatment_arms_pattern = r'"treatment_arms"\s*:\s*\['
            if re.search(treatment_arms_pattern, json_string):
                self.logger.info("Found treatment_arms pattern in JSON string. Attempting targeted recovery.")
                
                # Try to find the JSON object that contains treatment_arms
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
                                    if "treatment_arms" in parsed:
                                        self.logger.info("Successfully recovered complete JSON with treatment_arms.")
                                        return parsed
                                except json.JSONDecodeError:
                                    continue
            
            # Original fallback logic if targeted recovery fails
            best_match = None
            best_match_has_arms = False
            
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
                            has_treatment_arms = "treatment_arms" in parsed
                            
                            # Prioritize JSON objects that have treatment_arms
                            if has_treatment_arms and not best_match_has_arms:
                                best_match = substring
                                best_match_has_arms = True
                            elif (not best_match_has_arms and 
                                  (best_match is None or len(substring) > len(best_match))):
                                best_match = substring
                                
                        except json.JSONDecodeError:
                            continue # This substring is not valid JSON
            
            if best_match:
                self.logger.info(f"Successfully recovered a valid JSON object from the response. Has treatment_arms: {best_match_has_arms}")
                parsed = json.loads(best_match)
                
                # Debug logging for problematic cases
                if not best_match_has_arms:
                    self.logger.warning(f"Recovered JSON is missing treatment_arms. Keys found: {list(parsed.keys())}")
                    self.logger.debug(f"Original response length: {len(original_string)}")
                    self.logger.debug(f"Cleaned JSON length: {len(json_string)}")
                    self.logger.debug(f"Recovered JSON length: {len(best_match)}")
                    
                return parsed

        except Exception as fallback_e:
            self.logger.error(f"Fallback JSON parsing also failed: {fallback_e}")

        self.logger.error(f"Final JSON parsing attempt failed after all fallbacks.")
        self.logger.debug(f"Problematic JSON string after cleaning: {json_string[:500]}...")
        return None


    def _parse_json_response(self, response: str) -> dict:
        if not response:
            return {}
        
        # Use the new robust parser
        parsed_data = self._robust_parse_json(response)
        return parsed_data if parsed_data else {}

    def get_usage_summary(self) -> Dict[str, Any]:
        return {
            "total_requests": self.request_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": self.total_cost,
        }

    def print_usage_summary(self):
        summary = self.get_usage_summary()
        print("\n" + "=" * 50)
        print("OPENAI API USAGE SUMMARY")
        print("=" * 50)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Prompt Tokens: {summary['total_prompt_tokens']:,}")
        print(f"Total Completion Tokens: {summary['total_completion_tokens']:,}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.6f}")
        print("=" * 50)
