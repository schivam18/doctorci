import fitz  # PyMuPDF
from typing import Optional

from src.logger_config import get_logger, log_performance

@log_performance
def extract_clean_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extracts clean, ordered text from a PDF, preserving reading flow.

    This function uses `get_text("text")` which is reliable for handling
    multi-column layouts and providing a single, coherent block of text.
    It does not attempt to identify sections or tables, leaving that
    for downstream processing by the language model.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A single string containing the full text of the document, or None if
        an error occurs.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting clean text extraction from {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
        full_text = []
        for page_num, page in enumerate(doc):
            full_text.append(page.get_text("text"))
        
        doc.close()
        
        # Join all page texts into a single block
        final_text = "\n".join(full_text)
        logger.info(f"Successfully extracted {len(final_text)} characters from {pdf_path}")
        return final_text
    except Exception as e:
        logger.error(f"Error reading or processing {pdf_path} with clean extractor: {e}", exc_info=True)
        return None
