import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from src.logger_config import get_logger, log_performance
from src.repository import create_tables, insert_abstract

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def split_pdf_abstracts(text):
    """
    Split PDF abstracts using the pattern: abstract_id + session_type

    Pattern examples:
    - LBA9500 Oral Abstract Session
    - 9502 Oral Abstract Session
    - 9516 Rapid Oral Abstract Session
    - 9518 Poster Session
    """
    pattern = r"(?:LBA)?(\d{4,5})\s+((?:Oral Abstract|Rapid Oral Abstract|Poster)\s+Session)"
    matches = list(re.finditer(pattern, text))
    if not matches:
        return [text]  # No pattern found, return original text
    abstracts = []
    for i, match in enumerate(matches):
        start_pos = match.start()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        abstract_text = text[start_pos:end_pos].strip()
        abstract_id = match.group(1)
        session_type = match.group(2)
        full_id = match.group(0)
        abstracts.append(
            {
                "id": f"LBA{abstract_id}" if text[match.start() : match.start() + 3] == "LBA" else abstract_id,
                "session_type": session_type,
                "header": full_id,
                "text": abstract_text,
            }
        )
    return abstracts


def extract_text_from_pdf(pdf_path: str) -> Optional[List[str]]:
    """
    Extracts text from a single PDF file and splits it into multiple abstracts using PyMuPDF and a robust regex.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""

        # Extract text from each page with better error handling
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    full_text += page_text + "\n"
            except Exception as page_error:
                logger.warning(f"Error extracting text from page {page_num} in {pdf_path}: {page_error}")
                continue

        doc.close()

        if not full_text.strip():
            logger.warning(f"No text extracted from {pdf_path}")
            return None

        abstracts = split_pdf_abstracts(full_text)
        # Fix: handle both dict and string outputs
        if isinstance(abstracts[0], dict):
            return [abstract["text"] for abstract in abstracts]
        else:
            return abstracts
    except Exception as e:
        logger.error(f"Error reading {pdf_path}: {e}")
        return None


class PDFProcessor:
    def __init__(
        self,
        processed_files_record: str = "data/processed_files.json",
        abstract_pdf_path: str = "resources",
    ):
        """
        Initialize the PDFProcessor with configuration and logging.

        Parameters:
            processed_files_record (str): Path to the JSON file tracking processed PDFs
            abstract_pdf_path (str): Directory containing PDF files to process
        """
        self.logger = get_logger(__name__)
        self.logger.info("PDFProcessor initialized")
        self._processed_files_record = processed_files_record
        self._abstract_pdf_path = abstract_pdf_path

        # Ensure the processed files record exists
        if not os.path.exists(self._processed_files_record):
            os.makedirs(os.path.dirname(self._processed_files_record), exist_ok=True)
            with open(self._processed_files_record, "w") as f:
                json.dump([], f)
            self.logger.info(f"Created new processed files record at {self._processed_files_record}")

    def _load_processed_files(self) -> set:
        """Load the set of previously processed files."""
        try:
            with open(self._processed_files_record, "r") as f:
                return set(json.load(f))
        except Exception as e:
            self.logger.error(f"Error loading processed files record: {e}")
            return set()

    def _save_processed_files(self, processed_files: set) -> None:
        """Save the set of processed files."""
        try:
            with open(self._processed_files_record, "w") as f:
                json.dump(list(processed_files), f)
        except Exception as e:
            self.logger.error(f"Error saving processed files record: {e}")

    @log_performance
    def _extract_new_pdfs(self) -> Dict[str, Any]:
        """
        Extract text from new PDF files and insert them into the database.

        Returns:
            Dict[str, Any]: Statistics about the processing operation
        """
        # Ensure the Abstracts table exists
        create_tables()

        processed_files = self._load_processed_files()
        new_processed_files = set(processed_files)

        stats = {"total_files": 0, "processed_files": 0, "failed_files": 0, "failed_file_names": []}

        for filename in os.listdir(self._abstract_pdf_path):
            if not filename.lower().endswith(".pdf"):
                continue

            stats["total_files"] += 1

            if filename in processed_files:
                self.logger.info(f"Skipping already processed file: {filename}")
                continue

            pdf_path = os.path.join(self._abstract_pdf_path, filename)
            self.logger.info(f"Processing new file: {filename}")

            abstracts = extract_text_from_pdf(pdf_path)
            if abstracts:
                for abstract in abstracts:
                    try:
                        insert_abstract(filename, abstract)
                        stats["processed_files"] += 1
                        self.logger.info(f"Successfully processed abstract from {filename}")
                    except Exception as e:
                        self.logger.error(f"Error inserting abstract for {filename}: {e}")
                        stats["failed_files"] += 1
                        stats["failed_file_names"].append(filename)
                # Add filename to new_processed_files only if at least one abstract was processed
                new_processed_files.add(filename)
            else:
                stats["failed_files"] += 1
                stats["failed_file_names"].append(filename)

        self._save_processed_files(new_processed_files)
        return stats

    @log_performance
    def process_new_pdfs(self) -> Dict[str, Any]:
        """
        Process new PDFs and return processing statistics.

        Returns:
            Dict[str, Any]: Statistics about the processing operation
        """
        self.logger.info("Starting PDF processing")
        stats = self._extract_new_pdfs()

        self.logger.info(f"PDF processing complete:")
        self.logger.info(f"  - Total files found: {stats['total_files']}")
        self.logger.info(f"  - Successfully processed: {stats['processed_files']}")
        self.logger.info(f"  - Failed to process: {stats['failed_files']}")

        if stats["failed_files"] > 0:
            self.logger.warning("Failed files:")
            for filename in stats["failed_file_names"]:
                self.logger.warning(f"  - {filename}")

        return stats
