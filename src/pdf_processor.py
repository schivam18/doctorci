import os
import csv
import json
import PyPDF2

from src.repository import create_tables, insert_abstract


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a single PDF file.

    Parameters:
        pdf_path (str): The file path to the PDF file.

    Returns:
        str: The extracted text from the PDF.
    """
    text = ''
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    print(f"Warning: No text found on page {page_num + 1} in {pdf_path}.")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


class PDFProcessor:
    def __init__(
            self,
            processed_files_record='data/processed_files.json',
            abstract_pdf_path='resources',

    ):
        self._processed_files_record = processed_files_record
        self._abstract_pdf_path = abstract_pdf_path
        # Ensure the processed files record exists
        if not os.path.exists(self._processed_files_record):
            with open(self._processed_files_record, 'w') as f:
                json.dump([], f)

    def _load_processed_files(self):
        with open(self._processed_files_record, 'r') as f:
            return set(json.load(f))

    def _save_processed_files(self, processed_files):
        with open(self._processed_files_record, 'w') as f:
            json.dump(list(processed_files), f)

    def _extract_new_pdfs(self):
        """
        Extracts text from new PDF files that have not been processed yet and inserts them into the database.
        """
        # Ensure the Abstracts table exists
        create_tables()

        processed_files = self._load_processed_files()
        new_processed_files = set(processed_files)  # To track newly processed files
        for filename in os.listdir(self._abstract_pdf_path):
            if filename.lower().endswith('.pdf') and filename not in processed_files:
                pdf_path = os.path.join(self._abstract_pdf_path, filename)
                print(f"Processing new file: {filename}")
                text = extract_text_from_pdf(pdf_path)
                # Insert the extracted text into the database
                insert_abstract(filename, text)
                new_processed_files.add(filename)
        self._save_processed_files(new_processed_files)

    def process_new_pdfs(self):
        self._extract_new_pdfs()
