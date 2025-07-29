#!/usr/bin/env python3
"""
Enhanced batch processing script with comprehensive field coverage
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.append('src')

from openai_client import OpenAIClient
from enhanced_extractor import EnhancedClinicalExtractor
from logger_config import get_logger
from chunk_templates import CHUNK_FIELD_MAP

def process_single_markdown_comprehensive(markdown_path: str, output_dir: str, client: OpenAIClient,
                                       total_files: int, current_file: int) -> Dict[str, Any]:
    """
    Process single markdown file using comprehensive chunked approach
    """
    markdown_filename = os.path.basename(markdown_path)
    pdf_number = markdown_filename.split('.')[0]
    
    print(f"\n{'='*80}")
    print(f"📄 Processing with COMPREHENSIVE CHUNKED approach {current_file}/{total_files}: {markdown_filename}")
    print(f"{'='*80}")
    
    result = {
        "markdown_file": markdown_path,
        "pdf_number": pdf_number,
        "status": "failed",
        "approach": "comprehensive_chunked",
        "chunks_processed": 0,
        "arms_discovered": 0,
        "extraction_time": 0
    }
    
    start_time = time.time()
    
    try:
        # Read markdown content
        print(f"🔄 [{current_file}/{total_files}] Reading markdown content...")
        with open(markdown_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        if not full_text:
            result["error"] = "Empty markdown file"
            return result
        
        print(f"✅ [{current_file}/{total_files}] Content loaded: {len(full_text):,} characters")
        
        # Process with comprehensive chunked approach
        print(f"🔄 [{current_file}/{total_files}] Starting comprehensive chunked extraction...")
        
        extraction_data = client.extract_full_publication_comprehensive(full_text)
        
        if not extraction_data:
            result["error"] = "Comprehensive chunked extraction failed"
            return result
        
        # Update result with extraction metadata
        metadata = extraction_data.get("extraction_metadata", {})
        result.update({
            "status": "success",
            "chunks_processed": metadata.get("total_llm_calls", 0),
            "arms_discovered": metadata.get("arms_discovered", 0),
            "arms_processed": metadata.get("arms_processed", 0),
            "total_cost": metadata.get("total_cost", 0),
            "extraction_time": time.time() - start_time
        })
        
        # Add source information
        extraction_data["PDF number"] = f"{pdf_number}.pdf"
        extraction_data["Source markdown"] = markdown_filename
        
        # Save outputs
        print(f"🔄 [{current_file}/{total_files}] Saving comprehensive outputs...")
        
        # Save extraction result
        output_file = os.path.join(output_dir, f'comprehensive_extraction_{pdf_number}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extraction_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ [{current_file}/{total_files}] Comprehensive extraction completed!")
        print(f"   📊 Arms discovered: {result['arms_discovered']}")
        print(f"   🧩 Chunks processed: {result['chunks_processed']}")
        print(f"   💰 Cost: ${result['total_cost']:.6f}")
        print(f"   ⏱️  Time: {result['extraction_time']:.1f}s")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        result["extraction_time"] = time.time() - start_time
        print(f"❌ [{current_file}/{total_files}] Processing failed: {str(e)}")
        return result

def main():
    """Main batch processing with comprehensive approach"""
    
    # Setup directories
    markdown_dir = "input/marker_preprocessed"
    base_output_dir = "output"
    
    # Create comprehensive batch output directory
    batch_counter = 1
    while os.path.exists(os.path.join(base_output_dir, f"comprehensive_batch_{batch_counter}")):
        batch_counter += 1
    
    output_dir = os.path.join(base_output_dir, f"comprehensive_batch_{batch_counter}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get markdown files
    import glob
    markdown_files = sorted(glob.glob(os.path.join(markdown_dir, "*.md")))
    
    if not markdown_files:
        print("❌ No markdown files found")
        return
    
    # Calculate total fields
    total_fields = sum(len(fields) for fields in CHUNK_FIELD_MAP.values() if fields)
    
    print(f"🚀 COMPREHENSIVE Clinical Trial Data Extraction - Batch Processing")
    print(f"{'='*80}")
    print(f"📁 Input directory: {markdown_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Files to process: {len(markdown_files)}")
    print(f"🧩 Approach: Comprehensive chunked prompts (11 chunks per paper)")
    print(f"💎 Fields covered: {total_fields}")
    print(f"{'='*80}")
    
    # Initialize client
    client = OpenAIClient()
    logger = get_logger(__name__)
    
    # Process files
    results = []
    total_files = len(markdown_files)
    
    for i, markdown_path in enumerate(markdown_files, 1):
        result = process_single_markdown_comprehensive(
            markdown_path, output_dir, client, total_files, i
        )
        results.append(result)
        
        # Brief pause between files
        if i < total_files:
            print(f"\n⏳ Waiting 2 seconds before next file...")
            time.sleep(2)
    
    # Generate summary
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE BATCH PROCESSING SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total_files - successful
    total_time = sum(r["extraction_time"] for r in results)
    total_cost = sum(r.get("total_cost", 0) for r in results)
    total_chunks = sum(r.get("chunks_processed", 0) for r in results)
    total_arms = sum(r.get("arms_discovered", 0) for r in results)
    
    api_usage = client.get_usage_summary()
    
    print(f"📄 Total files processed: {total_files}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"🧩 Total chunks processed: {total_chunks}")
    print(f"🎯 Total arms discovered: {total_arms}")
    print(f"⏱️ Total processing time: {total_time:.1f} seconds")
    print(f"💰 Total cost: ${total_cost:.6f}")
    print(f"📊 Average chunks per paper: {total_chunks/max(1, successful):.1f}")
    print(f"🎯 Average arms per paper: {total_arms/max(1, successful):.1f}")
    print(f"💎 Total fields extracted: {total_fields}")
    
    # Save summary
    summary = {
        "batch_metadata": {
            "approach": "comprehensive_chunked",
            "processing_date": datetime.now().isoformat(),
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "total_chunks": total_chunks,
            "total_arms": total_arms,
            "total_time": total_time,
            "total_cost": total_cost,
            "total_fields": total_fields
        },
        "api_usage": api_usage,
        "results": results
    }
    
    summary_file = os.path.join(output_dir, 'comprehensive_batch_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    
    print(f"\n📄 Summary saved: {summary_file}")
    print(f"🎉 Comprehensive batch processing completed!")

if __name__ == "__main__":
    main()