#!/usr/bin/env python3
"""
Marker-Enhanced Clinical Trial Data Extraction Pipeline

This script integrates Marker PDF processing with the existing clinical trial
data extraction system for superior accuracy and quality.
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from marker_integration import MarkerPDFProcessor, MarkerIntegrationManager
from enhanced_extractor import EnhancedClinicalExtractor
from openai_client import OpenAIClient
from excel_generator import ExcelGenerator
from logger_config import get_logger, log_performance

class MarkerEnhancedPipeline:
    """
    Enhanced pipeline that uses Marker for PDF preprocessing and then
    applies clinical trial data extraction.
    """
    
    def __init__(self, use_llm: bool = False, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Marker-enhanced pipeline.
        
        Args:
            use_llm: Whether to use LLM enhancement for Marker processing
            config: Configuration dictionary
        """
        self.logger = get_logger(__name__)
        self.use_llm = use_llm
        self.config = config or {}
        
        # Initialize components
        self.marker_processor = MarkerPDFProcessor(
            use_llm=use_llm,
            force_ocr=False,
            debug=True,
            max_workers=2
        )
        
        self.extractor = EnhancedClinicalExtractor()
        self.openai_client = OpenAIClient()
        self.excel_generator = ExcelGenerator()
        
        # Create output directories
        self.output_dir = Path("input/marker_preprocessed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"🚀 Marker-Enhanced Pipeline initialized")
        self.logger.info(f"🤖 LLM Enhancement: {'Enabled' if use_llm else 'Disabled'}")
        self.logger.info(f"📁 Preprocessed output directory: {self.output_dir}")
    
    @log_performance
    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a single PDF through the Marker-enhanced pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing processing results
        """
        pdf_name = Path(pdf_path).stem
        self.logger.info(f"🔄 Processing PDF: {pdf_name}")
        
        try:
            # Step 1: Marker PDF Processing
            self.logger.info(f"📄 Step 1: Marker PDF Processing")
            marker_result = self._process_with_marker(pdf_path)
            
            if not marker_result.get('success', False):
                raise RuntimeError(f"Marker processing failed for {pdf_name}")
            
            # Step 2: Clinical Trial Data Extraction
            self.logger.info(f"🔬 Step 2: Clinical Trial Data Extraction")
            extraction_result = self._extract_clinical_data(marker_result)
            
            # Step 3: Quality Assessment
            self.logger.info(f"📊 Step 3: Quality Assessment")
            quality_result = self._assess_quality(marker_result, extraction_result)
            
            # Combine results
            final_result = {
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'marker_processing': marker_result,
                'clinical_extraction': extraction_result,
                'quality_assessment': quality_result,
                'success': True,
                'processing_time': time.time(),
                'use_llm': self.use_llm
            }
            
            # Save individual results
            self._save_results(pdf_name, final_result)
            
            self.logger.info(f"✅ Successfully processed {pdf_name}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process {pdf_name}: {e}")
            return {
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time()
            }
    
    def _process_with_marker(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF with Marker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.marker_processor.process_single_pdf(pdf_path, temp_dir)
            
            # Add additional metadata
            result['processing_mode'] = 'marker_enhanced'
            result['use_llm'] = self.use_llm
            result['markdown_quality_score'] = self._calculate_markdown_quality(result.get('markdown_content', ''))
            
            return result
    
    def _extract_clinical_data(self, marker_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clinical trial data from Marker output."""
        markdown_content = marker_result.get('markdown_content', '')
        
        if not markdown_content:
            raise ValueError("No markdown content available for extraction")
        
        # Use existing extraction pipeline with validation
        extraction_result = self.extractor.extract_with_validation(markdown_content)
        
        # Add metadata
        extraction_result['source'] = 'marker_enhanced'
        extraction_result['markdown_length'] = len(markdown_content)
        extraction_result['extraction_timestamp'] = datetime.now().isoformat()
        
        return extraction_result
    
    def _assess_quality(self, marker_result: Dict[str, Any], extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of processing and extraction."""
        markdown_content = marker_result.get('markdown_content', '')
        
        quality_metrics = {
            'markdown_quality': self._calculate_markdown_quality(markdown_content),
            'clinical_keywords_found': self._count_clinical_keywords(markdown_content),
            'table_structures': markdown_content.count('|'),
            'section_headers': markdown_content.count('#'),
            'nct_numbers': markdown_content.count('NCT'),
            'extraction_fields_filled': len([v for v in extraction_result.values() if v and v != 'Not mentioned']),
            'processing_success': True
        }
        
        return quality_metrics
    
    def _calculate_markdown_quality(self, content: str) -> float:
        """Calculate a quality score for the markdown content."""
        if not content:
            return 0.0
        
        # Quality indicators
        indicators = {
            'has_structure': len(content.split('\n')) > 50,
            'has_headers': content.count('#') > 10,
            'has_content': len(content) > 10000,
            'has_tables': content.count('|') > 100,
            'has_clinical_terms': any(term in content.lower() for term in ['clinical', 'trial', 'patient', 'treatment'])
        }
        
        return sum(indicators.values()) / len(indicators) * 100
    
    def _count_clinical_keywords(self, content: str) -> int:
        """Count clinical trial keywords in the content."""
        clinical_keywords = [
            'clinical trial', 'phase', 'randomized', 'placebo', 'efficacy',
            'safety', 'adverse events', 'survival', 'response rate', 'NCT',
            'patient', 'treatment', 'dose', 'regimen', 'outcome'
        ]
        
        return sum(1 for keyword in clinical_keywords if keyword.lower() in content.lower())
    
    def _save_results(self, pdf_name: str, result: Dict[str, Any]):
        """Save processing results to files."""
        
        # Save JSON result with simplified naming
        json_path = self.output_dir / f"{pdf_name}.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Save markdown content with simplified naming
        markdown_content = result.get('marker_processing', {}).get('markdown_content', '')
        if markdown_content:
            md_path = self.output_dir / f"{pdf_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        self.logger.info(f"💾 Results saved: {json_path}")
    
    @log_performance
    def process_batch_pdfs(self, pdf_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple PDFs through the Marker-enhanced pipeline.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of processing results
        """
        self.logger.info(f"🚀 Starting batch processing of {len(pdf_paths)} PDFs")
        
        results = []
        successful = 0
        failed = 0
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            self.logger.info(f"📄 Processing {i}/{len(pdf_paths)}: {Path(pdf_path).name}")
            
            try:
                result = self.process_single_pdf(pdf_path)
                results.append(result)
                
                if result.get('success', False):
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to process {pdf_path}: {e}")
                results.append({
                    'pdf_path': pdf_path,
                    'pdf_name': Path(pdf_path).stem,
                    'success': False,
                    'error': str(e)
                })
                failed += 1
        
        # Generate summary report
        self._generate_summary_report(results, successful, failed)
        
        self.logger.info(f"✅ Batch processing completed: {successful} successful, {failed} failed")
        return results
    
    def _generate_summary_report(self, results: List[Dict[str, Any]], successful: int, failed: int):
        """Generate a summary report of batch processing."""
        report_path = self.output_dir / "summary.json"
        
        # Calculate aggregate metrics
        total_processing_time = sum(r.get('processing_time', 0) for r in results if r.get('success'))
        avg_quality_score = sum(r.get('quality_assessment', {}).get('markdown_quality', 0) for r in results if r.get('success')) / max(successful, 1)
        
        summary = {
            'timestamp': timestamp,
            'total_pdfs': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(results) * 100 if results else 0,
            'total_processing_time': total_processing_time,
            'average_quality_score': avg_quality_score,
            'use_llm': self.use_llm,
            'results': results
        }
        
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"📊 Summary report saved: {report_path}")
        
        # Print summary to console
        print(f"\n" + "="*60)
        print(f"📊 MARKER-ENHANCED PIPELINE SUMMARY")
        print(f"="*60)
        print(f"📄 Total PDFs processed: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total processing time: {total_processing_time:.1f} seconds")
        print(f"🎯 Average quality score: {avg_quality_score:.1f}%")
        print(f"🤖 LLM Enhancement: {'Enabled' if self.use_llm else 'Disabled'}")
        print(f"📁 Preprocessed files saved to: {self.output_dir}")
        print(f"="*60)

def main():
    """Main function to run the Marker-enhanced pipeline."""
    print("🚀 Marker-Enhanced Clinical Trial Data Extraction Pipeline")
    print("=" * 70)
    
    # Get PDF files from resources directory
    resources_dir = Path("resources")
    pdf_files = list(resources_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in resources directory")
        return False
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Ask user for LLM preference
    use_llm = input("\n🤖 Use LLM enhancement? (y/N): ").lower() == 'y'
    
    if use_llm:
        print("✅ LLM enhancement enabled - higher accuracy, longer processing time")
    else:
        print("⚡ Basic processing enabled - faster processing, good accuracy")
    
    # Initialize pipeline
    pipeline = MarkerEnhancedPipeline(use_llm=use_llm)
    
    # Process all PDFs
    print(f"\n🔄 Starting processing of {len(pdf_files)} PDFs...")
    results = pipeline.process_batch_pdfs([str(pdf) for pdf in pdf_files])
    
    print(f"\n🎉 Processing completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 