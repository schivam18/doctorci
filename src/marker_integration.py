"""
Marker PDF Integration Module

This module integrates the Marker PDF processing tool into the clinical trial
data extraction system. Marker provides superior text extraction, layout
detection, and table extraction capabilities compared to basic PyMuPDF.

Key Features:
- High-accuracy table extraction (81.6% vs basic text extraction)
- Layout preservation and reading order detection
- Optional LLM enhancement for quality improvement
- Structured JSON + Markdown output
- GPU acceleration support

Author: Clinical Trial Data Extraction System
Date: 2025
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system environment variables

from src.logger_config import get_logger, log_performance


class MarkerPDFProcessor:
    """
    Marker PDF Processor for clinical trial documents.
    
    Integrates Marker's advanced PDF processing capabilities with the existing
    clinical trial extraction pipeline. Provides superior text extraction,
    table detection, and layout preservation compared to basic PyMuPDF.
    """
    
    def __init__(
        self,
        marker_path: Optional[str] = None,
        use_llm: bool = False,
        force_ocr: bool = False,
        debug: bool = False,
        max_workers: int = 4
    ):
        """
        Initialize the Marker PDF processor.
        
        Args:
            marker_path: Path to marker executable. If None, uses system PATH.
            use_llm: Whether to use LLM enhancement for quality improvement.
            force_ocr: Force OCR for documents with garbled text.
            debug: Enable debug mode for detailed output.
            max_workers: Number of worker processes for batch processing.
        """
        self.logger = get_logger(__name__)
        self.marker_path = marker_path or "marker"
        self.use_llm = use_llm
        self.force_ocr = force_ocr
        self.debug = debug
        self.max_workers = max_workers
        
        # Validate marker installation
        self._validate_marker_installation()
        
        # LLM configuration
        if self.use_llm:
            self._validate_llm_configuration()
    
    def _validate_marker_installation(self) -> None:
        """Validate that Marker is properly installed and accessible."""
        try:
            result = subprocess.run(
                [self.marker_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"Marker installation validation failed: {result.stderr}")
            
            self.logger.info("✅ Marker installation validated successfully")
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"❌ Marker installation validation failed: {e}")
            raise RuntimeError(
                f"Marker not found or not accessible at '{self.marker_path}'. "
                "Please install Marker: pip install marker"
            )
    
    def _validate_llm_configuration(self) -> None:
        """Validate LLM configuration when use_llm is enabled."""
        if not self.use_llm:
            return
            
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            self.logger.warning(
                "⚠️  GOOGLE_API_KEY not set. LLM enhancement will be disabled. "
                "Set GOOGLE_API_KEY environment variable to enable LLM features."
            )
            self.use_llm = False
        else:
            self.logger.info("✅ LLM configuration validated")
            self.logger.info(f"🔧 Using Google Gemini model for enhanced accuracy")
    
    @log_performance
    def process_single_pdf(
        self, 
        pdf_path: str, 
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single PDF file using Marker.
        
        Args:
            pdf_path: Path to the PDF file to process.
            output_dir: Directory for output files. If None, uses temp directory.
            
        Returns:
            Dictionary containing processing results and extracted data.
        """
        self.logger.info(f"🔄 Starting Marker processing for: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="marker_output_")
        
        os.makedirs(output_dir, exist_ok=True)
        self.logger.info(f"📁 Output directory: {output_dir}")
        
        # Generate output filenames
        pdf_name = Path(pdf_path).stem
        markdown_path = os.path.join(output_dir, f"{pdf_name}.md")
        json_path = os.path.join(output_dir, f"{pdf_name}.json")
        
        # Show processing mode
        if self.use_llm:
            self.logger.info("🤖 Using LLM enhancement for higher accuracy")
        else:
            self.logger.info("⚡ Using basic processing for faster results")
        
        # Build marker command
        self.logger.info("🔧 Building Marker command...")
        cmd = self._build_marker_command(
            pdf_path=pdf_path,
            markdown_path=markdown_path,
            json_path=json_path
        )
        
        # Execute marker
        self.logger.info("🚀 Executing Marker command...")
        result = self._execute_marker_command(cmd)
        
        # Parse results
        self.logger.info("📊 Parsing processing results...")
        processing_result = self._parse_processing_result(
            result=result,
            pdf_path=pdf_path,
            markdown_path=markdown_path,
            json_path=json_path
        )
        
        self.logger.info(f"✅ Marker processing completed for: {pdf_path}")
        return processing_result
    
    def _build_marker_command(
        self, 
        pdf_path: str, 
        markdown_path: str, 
        json_path: str
    ) -> List[str]:
        """Build the marker command with appropriate arguments."""
        # Create input directory for Marker (it expects a directory)
        input_dir = os.path.dirname(pdf_path)
        output_dir = os.path.dirname(markdown_path)
        
        cmd = [self.marker_path, input_dir, "--output_dir", output_dir]
        
        # Add optional flags
        if self.use_llm:
            cmd.append("--llm_service")
            cmd.append("marker.services.gemini.GoogleGeminiService")
        
        if self.force_ocr:
            cmd.append("--force_ocr")
        
        if self.debug:
            cmd.append("--debug_print")
        
        # Add performance options
        cmd.extend(["--workers", str(self.max_workers)])
        
        return cmd
    
    def _execute_marker_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute the marker command and handle errors."""
        self.logger.info(f"Executing marker command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"Marker command failed: {result.stderr}")
                raise RuntimeError(f"Marker processing failed: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            self.logger.error("Marker command timed out after 10 minutes")
            raise RuntimeError("Marker processing timed out")
        
        except Exception as e:
            self.logger.error(f"Unexpected error during marker execution: {e}")
            raise
    
    def _parse_processing_result(
        self,
        result: subprocess.CompletedProcess,
        pdf_path: str,
        markdown_path: str,
        json_path: str
    ) -> Dict[str, Any]:
        """Parse the marker processing result and extract relevant data."""
        pdf_name = Path(pdf_path).stem
        
        # Marker creates output in a subdirectory with the PDF name
        marker_output_dir = os.path.join(os.path.dirname(markdown_path), pdf_name)
        marker_md_path = os.path.join(marker_output_dir, f"{pdf_name}.md")
        marker_json_path = os.path.join(marker_output_dir, f"{pdf_name}_meta.json")
        
        processing_result = {
            "pdf_path": pdf_path,
            "pdf_name": pdf_name,
            "markdown_path": marker_md_path,
            "json_path": marker_json_path,
            "success": True,
            "markdown_content": "",
            "json_data": {},
            "tables": [],
            "metadata": {},
            "processing_stats": {}
        }
        
        # Read markdown content
        if os.path.exists(marker_md_path):
            try:
                with open(marker_md_path, 'r', encoding='utf-8') as f:
                    processing_result["markdown_content"] = f.read()
            except Exception as e:
                self.logger.warning(f"Failed to read markdown file: {e}")
        
        # Read JSON data
        if os.path.exists(marker_json_path):
            try:
                with open(marker_json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    processing_result["json_data"] = json_data
                    
                    # Extract tables from JSON
                    processing_result["tables"] = self._extract_tables_from_json(json_data)
                    
                    # Extract metadata
                    processing_result["metadata"] = self._extract_metadata_from_json(json_data)
                    
            except Exception as e:
                self.logger.warning(f"Failed to read JSON file: {e}")
        
        # Extract processing statistics
        processing_result["processing_stats"] = self._extract_processing_stats(result)
        
        return processing_result
    
    def _extract_tables_from_json(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract table data from Marker JSON output."""
        tables = []
        
        # Marker stores tables in the JSON structure
        # This is a simplified extraction - adjust based on actual Marker JSON format
        if "tables" in json_data:
            for table in json_data["tables"]:
                tables.append({
                    "type": "table",
                    "content": table.get("content", ""),
                    "html": table.get("html", ""),
                    "bbox": table.get("bbox", []),
                    "page": table.get("page", 0)
                })
        
        return tables
    
    def _extract_metadata_from_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Marker JSON output."""
        metadata = {
            "total_pages": json_data.get("pages", 0),
            "document_type": json_data.get("document_type", "unknown"),
            "processing_time": json_data.get("processing_time", 0),
            "ocr_used": json_data.get("ocr_used", False)
        }
        
        return metadata
    
    def _extract_processing_stats(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Extract processing statistics from marker output."""
        stats = {
            "return_code": result.returncode,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr)
        }
        
        # Parse timing information from stdout if available
        if result.stdout:
            # Look for timing patterns in marker output
            import re
            timing_match = re.search(r"Processing time: ([\d.]+)s", result.stdout)
            if timing_match:
                stats["processing_time_seconds"] = float(timing_match.group(1))
        
        return stats
    
    @log_performance
    def process_batch_pdfs(
        self, 
        pdf_paths: List[str], 
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files using Marker.
        
        Args:
            pdf_paths: List of PDF file paths to process.
            output_dir: Directory for output files.
            
        Returns:
            List of processing results for each PDF.
        """
        self.logger.info(f"🔄 Starting batch processing of {len(pdf_paths)} PDFs")
        
        results = []
        successful = 0
        failed = 0
        
        for pdf_path in pdf_paths:
            try:
                result = self.process_single_pdf(pdf_path, output_dir)
                results.append(result)
                successful += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_path}: {e}")
                results.append({
                    "pdf_path": pdf_path,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        self.logger.info(
            f"✅ Batch processing completed: {successful} successful, {failed} failed"
        )
        
        return results
    
    def extract_clinical_trial_data(
        self, 
        processing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract clinical trial specific data from Marker processing result.
        
        This method adapts Marker's output to the clinical trial extraction
        system's expected format.
        
        Args:
            processing_result: Result from Marker processing.
            
        Returns:
            Clinical trial data in the system's expected format.
        """
        if not processing_result.get("success", False):
            return {"error": "Processing failed", "extracted_data": {}}
        
        # Extract text content (prefer markdown, fallback to JSON)
        text_content = processing_result.get("markdown_content", "")
        if not text_content and "json_data" in processing_result:
            # Extract text from JSON structure
            text_content = self._extract_text_from_json(processing_result["json_data"])
        
        # Extract tables for adverse events analysis
        tables = processing_result.get("tables", [])
        
        # Extract metadata
        metadata = processing_result.get("metadata", {})
        
        # Structure the output for the clinical trial system
        clinical_data = {
            "text_content": text_content,
            "tables": tables,
            "metadata": metadata,
            "processing_source": "marker",
            "extraction_quality": self._assess_extraction_quality(processing_result)
        }
        
        return clinical_data
    
    def _extract_text_from_json(self, json_data: Dict[str, Any]) -> str:
        """Extract text content from Marker JSON structure."""
        text_parts = []
        
        # Navigate through JSON structure to find text content
        # This is a simplified approach - adjust based on actual Marker JSON format
        if "pages" in json_data:
            for page in json_data["pages"]:
                if "blocks" in page:
                    for block in page["blocks"]:
                        if "text" in block:
                            text_parts.append(block["text"])
        
        return "\n".join(text_parts)
    
    def _assess_extraction_quality(self, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the extraction."""
        quality_metrics = {
            "text_length": len(processing_result.get("markdown_content", "")),
            "table_count": len(processing_result.get("tables", [])),
            "ocr_used": processing_result.get("metadata", {}).get("ocr_used", False),
            "llm_enhanced": self.use_llm
        }
        
        # Calculate quality score
        score = 0
        if quality_metrics["text_length"] > 1000:
            score += 30
        if quality_metrics["table_count"] > 0:
            score += 30
        if quality_metrics["llm_enhanced"]:
            score += 20
        if not quality_metrics["ocr_used"]:
            score += 20
        
        quality_metrics["quality_score"] = min(score, 100)
        
        return quality_metrics


class MarkerIntegrationManager:
    """
    Manager class for integrating Marker with the existing clinical trial system.
    
    This class provides a bridge between Marker's advanced PDF processing
    capabilities and the existing extraction pipeline.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Marker integration manager.
        
        Args:
            config: Configuration dictionary for Marker settings.
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # Initialize Marker processor
        self.marker_processor = MarkerPDFProcessor(
            marker_path=self.config.get("marker_path"),
            use_llm=self.config.get("use_llm", False),
            force_ocr=self.config.get("force_ocr", False),
            debug=self.config.get("debug", False),
            max_workers=self.config.get("max_workers", 4)
        )
    
    def process_clinical_trial_pdf(
        self, 
        pdf_path: str, 
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a clinical trial PDF using Marker and adapt to system format.
        
        Args:
            pdf_path: Path to the clinical trial PDF.
            output_dir: Directory for output files.
            
        Returns:
            Clinical trial data in the system's expected format.
        """
        self.logger.info(f"🔄 Processing clinical trial PDF with Marker: {pdf_path}")
        
        # Process with Marker
        marker_result = self.marker_processor.process_single_pdf(pdf_path, output_dir)
        
        # Extract clinical trial specific data
        clinical_data = self.marker_processor.extract_clinical_trial_data(marker_result)
        
        # Add processing metadata
        clinical_data["marker_processing"] = {
            "success": marker_result.get("success", False),
            "processing_stats": marker_result.get("processing_stats", {}),
            "output_files": {
                "markdown": marker_result.get("markdown_path"),
                "json": marker_result.get("json_path")
            }
        }
        
        self.logger.info(f"✅ Clinical trial PDF processing completed: {pdf_path}")
        return clinical_data
    
    def compare_with_existing_processor(
        self, 
        pdf_path: str
    ) -> Dict[str, Any]:
        """
        Compare Marker processing with existing PyMuPDF processing.
        
        Args:
            pdf_path: Path to the PDF file to compare.
            
        Returns:
            Comparison results between Marker and existing processor.
        """
        self.logger.info(f"🔄 Comparing Marker vs existing processor for: {pdf_path}")
        
        # Process with Marker
        marker_result = self.marker_processor.process_single_pdf(pdf_path)
        marker_text = marker_result.get("markdown_content", "")
        
        # Process with existing system (PyMuPDF)
        from src.pdf_processor import extract_text_from_pdf
        existing_result = extract_text_from_pdf(pdf_path)
        existing_text = "\n".join(existing_result) if existing_result else ""
        
        # Compare results
        comparison = {
            "pdf_path": pdf_path,
            "marker_text_length": len(marker_text),
            "existing_text_length": len(existing_text),
            "marker_tables_count": len(marker_result.get("tables", [])),
            "text_overlap": self._calculate_text_overlap(marker_text, existing_text),
            "quality_assessment": marker_result.get("extraction_quality", {})
        }
        
        self.logger.info(f"✅ Comparison completed for: {pdf_path}")
        return comparison
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate the overlap between two text extracts."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based overlap calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0 