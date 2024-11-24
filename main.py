# main.py

import logging
import json  # Import the json module
from src.openai_client import OpenAIClient
from src.pdf_processor import PDFProcessor
from src.prompts import generate_extraction_prompt
from src.repository import get_abstract_by_id
from src.data_saver import save_response_to_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ABSTRACT_IDS_TO_PROCESS = [1,2,3,4,5]  # You can update this list or parameterize it


def process_pdfs():
    """Process new PDFs using the PDFProcessor."""
    logger.info("Processing new PDFs...")
    pdf_processor = PDFProcessor()
    pdf_processor.process_new_pdfs()
    logger.info("PDF processing complete.")


def retrieve_abstract(abstract_id):
    """Retrieve an abstract by its ID."""
    logger.info(f"Retrieving abstract with ID {abstract_id}...")
    abstract = get_abstract_by_id(abstract_id)
    if not abstract:
        logger.warning(f"No abstract found with ID {abstract_id}.")
        return None
    logger.info(f"Abstract {abstract_id} retrieved successfully.")
    return abstract['abstract_text']


def prepare_messages(abstract_text):
    """Prepare messages for the OpenAI API."""
    logger.info("Generating extraction prompt...")
    extraction_prompt = generate_extraction_prompt(abstract_text)
    messages = [
        {
            "role": "system",
            "content": (
                "You are acting as a **Scientific Paper Data Extractor** specializing in "
                "the pharmacy and medical field."
            )
        },
        {
            "role": "user",
            "content": extraction_prompt
        }
    ]
    logger.info("Messages prepared for OpenAI API.")
    return messages


def get_openai_response(messages):
    """Get response from the OpenAI API."""
    logger.info("Initializing OpenAI client and requesting completion...")
    client = OpenAIClient()
    response = client.get_chat_completion(messages)
    logger.info("Received response from OpenAI API.")
    return response


def verify_json(response_content):
    """Verify if the response content is valid JSON."""
    try:
        # Attempt to parse the response content as JSON
        parsed_json = json.loads(response_content)
        logger.info("The response is valid JSON.")
        return True, parsed_json
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {e}")
        return False, None


def main():
    """Main function to process PDFs and interact with OpenAI API."""
    try:
        # Step 1: Process new PDFs
        process_pdfs()

        # Step 2: Process each abstract
        for abstract_id in ABSTRACT_IDS_TO_PROCESS:
            # Retrieve abstract text
            abstract_text = retrieve_abstract(abstract_id)
            if not abstract_text:
                continue  # Skip if abstract not found

            # Prepare messages for OpenAI API
            messages = prepare_messages(abstract_text)

            # Get response from OpenAI API
            response = get_openai_response(messages)

            # Extract content from the response
            response_content = response.content.strip()  # Remove leading/trailing whitespace

            # Verify if the response content is valid JSON
            is_valid_json, parsed_json = verify_json(response_content)

            if is_valid_json:
                # Pretty-print the parsed JSON
                pretty_json = json.dumps(parsed_json, indent=4)
                logger.info(f"Parsed JSON content:\n{pretty_json}")
                # You can proceed to use 'parsed_json' in your application
            else:
                # Handle the invalid JSON response
                logger.warning("The response is not valid JSON. Attempting to clean up the response...")
                # Print the invalid JSON (raw response content)
                logger.warning(f"Invalid JSON content:\n{response_content}")

                # Optional: Attempt to clean up the response
                cleaned_content = attempt_to_clean_json(response_content)
                if cleaned_content:
                    is_valid_json, parsed_json = verify_json(cleaned_content)
                    if is_valid_json:
                        # Pretty-print the cleaned and parsed JSON
                        pretty_json = json.dumps(parsed_json, indent=4)
                        logger.info("Successfully cleaned and parsed the JSON response.")
                        logger.info(f"Cleaned JSON content:\n{pretty_json}")
                        # Proceed with the cleaned and parsed JSON
                        save_response_to_db(abstract_text, cleaned_content)
                    else:
                        logger.error("Failed to clean and parse the JSON response.")
                        logger.error(f"Cleaned content that failed to parse:\n{cleaned_content}")
                else:
                    logger.error("Could not clean the response to valid JSON.")
                    logger.error(f"Original invalid content:\n{response_content}")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        # Additional error handling as needed


def attempt_to_clean_json(response_content):
    """Attempt to clean up the response content to make it valid JSON."""
    # Implement cleaning logic, e.g., removing extraneous text
    # For this example, we'll assume the JSON content is between a pair of triple backticks
    import re

    logger.info("Attempting to extract JSON snippet from the response...")

    # Use a regular expression to find JSON content within code blocks
    match = re.search(r'```json\s*(\{.*?})\s*```', response_content, re.DOTALL)
    if match:
        json_snippet = match.group(1)
        logger.info("Extracted JSON snippet from code block.")
        return json_snippet
    else:
        logger.warning("No JSON code block found in the response.")
        return None


if __name__ == "__main__":
    main()
