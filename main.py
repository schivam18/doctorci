import logging
import os
import time
import json
from typing import Dict, List, Any

from src.excel_generator import generate_full_pub_csv_and_excel
from src.full_pub_processor import extract_clean_text_from_pdf
from src.openai_client import OpenAIClient
from src.therapy_classifier import classify_therapy
from src.logger_config import setup_logging
from datetime import datetime

def load_processed_files() -> Dict[str, Any]:
    """Load the processed files tracking data."""
    processed_files_path = "data/processed_files.json"
    try:
        if os.path.exists(processed_files_path):
            with open(processed_files_path, 'r') as f:
                return json.load(f)
        else:
            # Create fresh tracking data if file doesn't exist
            return {
                "processed_files": [],
                "failed_files": [],
                "last_processed": None,
                "total_processed": 0,
                "total_failed": 0
            }
    except Exception as e:
        logging.error(f"Error loading processed files: {e}")
        return {
            "processed_files": [],
            "failed_files": [],
            "last_processed": None,
            "total_processed": 0,
            "total_failed": 0
        }

def save_processed_files(tracking_data: Dict[str, Any]) -> None:
    """Save the processed files tracking data."""
    processed_files_path = "data/processed_files.json"
    try:
        os.makedirs(os.path.dirname(processed_files_path), exist_ok=True)
        with open(processed_files_path, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving processed files: {e}")

def update_tracking(tracking_data: Dict[str, Any], pdf_file: str, success: bool = True) -> None:
    """Update the tracking data with a processed file."""
    current_time = datetime.now().isoformat()
    
    if success:
        if pdf_file not in tracking_data["processed_files"]:
            tracking_data["processed_files"].append(pdf_file)
            tracking_data["total_processed"] += 1
        tracking_data["last_processed"] = current_time
    else:
        if pdf_file not in tracking_data["failed_files"]:
            tracking_data["failed_files"].append(pdf_file)
            tracking_data["total_failed"] += 1

def main():
    """
    Main function to orchestrate the full publication data extraction process.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    try:
        # Determine processing mode
        process_mode = os.environ.get('PROCESS_MODE', 'full_pub').lower()

        if process_mode == 'full_pub':
            logger.info("Processing in full publication mode...")
            
            # Load processed files tracking
            tracking_data = load_processed_files()
            processed_files = set(tracking_data["processed_files"])
            failed_files = set(tracking_data["failed_files"])
            
            logger.info(f"Previously processed files: {len(processed_files)}")
            logger.info(f"Previously failed files: {len(failed_files)}")
            
            all_results = []
            pdf_folder = "resources"
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
            new_files = [f for f in pdf_files if f not in processed_files and f not in failed_files]
            
            if not new_files:
                logger.info("No new PDF files to process.")
                return
            
            logger.info(f"Found {len(new_files)} new PDF files to process")
            
            client = OpenAIClient()

            for pdf_file in new_files:
                if "nccn" in pdf_file.lower():
                    logger.info(f"Skipping NCCN guideline file: {pdf_file}")
                    continue

                pdf_path = os.path.join(pdf_folder, pdf_file)
                logger.info(f"--- Processing: {pdf_file} ---")
                
                try:
                    full_text = extract_clean_text_from_pdf(pdf_path)
                    if not full_text:
                        logger.warning(f"Could not extract text from {pdf_file}. Skipping.")
                        update_tracking(tracking_data, pdf_file, success=False)
                        continue
                    
                    extracted_data = client.extract_publication_data(full_text)
                    
                    if not extracted_data or not extracted_data.get("NCT Number"):
                        logger.warning(f"No NCT Number found for {pdf_file}. Discarding results.")
                        update_tracking(tracking_data, pdf_file, success=False)
                        continue

                    # Add PDF filename to the extracted data
                    extracted_data["PDF number"] = pdf_file
                    logger.info(f"Added PDF number: {pdf_file} to extracted data")

                    # Post-process to classify therapy type for each arm
                    if "treatment_arms" in extracted_data and extracted_data["treatment_arms"]:
                        for arm in extracted_data["treatment_arms"]:
                            generic_name = arm.get("Generic name", "")
                            arm["Type of therapy"] = classify_therapy(generic_name)

                    all_results.append(extracted_data)
                    update_tracking(tracking_data, pdf_file, success=True)
                    logger.info(f"Successfully processed and extracted data for {pdf_file}")

                except Exception as e:
                    logger.error(f"Failed to process {pdf_file}: {e}", exc_info=True)
                    update_tracking(tracking_data, pdf_file, success=False)
            
            # Save updated tracking data
            save_processed_files(tracking_data)
            
            if all_results:
                logger.info(f"Total publications successfully processed: {len(all_results)}")
                today = datetime.now().strftime('%Y-%m-%d')
                output_filename_base = f"{today}_full_pub_data"
                generate_full_pub_csv_and_excel(all_results, output_filename_base, output_dir)
            else:
                logger.warning("No data was extracted from any of the PDFs.")
            
            # Log final statistics
            logger.info(f"Processing complete:")
            logger.info(f"  - Total processed files: {tracking_data['total_processed']}")
            logger.info(f"  - Total failed files: {tracking_data['total_failed']}")
            logger.info(f"  - Last processed: {tracking_data['last_processed']}")
            
            client.print_usage_summary()

        else:
            logger.error(f"Invalid PROCESS_MODE: {process_mode}. Please use 'full_pub'.")

    except Exception as e:
        logger.critical(f"A critical error occurred in the main application: {e}", exc_info=True)
    finally:
        end_time = time.time()
        logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()