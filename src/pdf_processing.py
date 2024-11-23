import os
import csv
import json
import PyPDF2


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
            output_csv='data/processed_abstracts.csv',

    ):
        self._processed_files_record = processed_files_record
        self._abstract_pdf_path = abstract_pdf_path
        self.output_csv = output_csv
        # Ensure the processed files record exists
        if not os.path.exists(self._processed_files_record):
            with open(self._processed_files_record, 'w') as f:
                json.dump([], f)

    def save_texts_to_csv(self, pdf_texts):
        # Modify to append to the CSV if it already exists
        file_exists = os.path.isfile(self.output_csv)
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(self.output_csv)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(self.output_csv, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['filename', 'text']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                for pdf in pdf_texts:
                    writer.writerow(pdf)
            print(f"Extracted texts have been saved to {self.output_csv}")
        except Exception as e:
            print(f"Error writing to CSV file {self.output_csv}: {e}")

    def _load_processed_files(self):
        with open(self._processed_files_record, 'r') as f:
            return set(json.load(f))

    def _save_processed_files(self, processed_files):
        with open(self._processed_files_record, 'w') as f:
            json.dump(list(processed_files), f)

    def _extract_new_pdfs(self, pdf_folder):
        """
        Extracts text from new PDF files that have not been processed yet.
        """
        processed_files = self._load_processed_files()
        new_pdfs = []
        for filename in os.listdir(pdf_folder):
            if filename.lower().endswith('.pdf') and filename not in processed_files:
                pdf_path = os.path.join(pdf_folder, filename)
                print(f"Processing new file: {filename}")
                text = extract_text_from_pdf(pdf_path)
                new_pdfs.append({'filename': filename, 'text': text})
                processed_files.add(filename)
        self._save_processed_files(processed_files)
        return new_pdfs

    def process_new_pdfs_to_csv(self, pdf_folder='resources', output_csv=''):
        new_pdfs = self._extract_new_pdfs(pdf_folder)
        if new_pdfs:
            self.save_texts_to_csv(new_pdfs)
        else:
            print("No new PDFs to process.")
