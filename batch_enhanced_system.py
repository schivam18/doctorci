#!/usr/bin/env python3
"""
Batch processing script for enhanced clinical trial data extraction system.
Processes all Marker-enhanced markdown files with progress tracking.
"""

import os
import sys
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any
import glob

# Add src to path
sys.path.append('src')

# No longer need PDF extraction since we're using pre-processed markdown
from openai_client import OpenAIClient
from enhanced_extractor import EnhancedClinicalExtractor
from logger_config import get_logger

def save_to_csv(data: Dict[str, Any], output_file: str) -> int:
    """Save data to CSV format with proper encoding"""
    if not data:
        return 0
    
    # Flatten the data structure for CSV
    rows = []
    
    # Handle main fields (non-treatment arm fields)
    main_row = {}
    treatment_arms = data.get('treatment_arms', [])
    
    # Add all non-treatment arm fields
    for key, value in data.items():
        if key != 'treatment_arms':
            if isinstance(value, (list, dict)):
                main_row[key] = json.dumps(value, ensure_ascii=False)
            else:
                main_row[key] = str(value) if value is not None else ''
    
    # If no treatment arms, just save the main row
    if not treatment_arms:
        rows.append(main_row)
    else:
        # For each treatment arm, create a row with main data + arm data
        for i, arm in enumerate(treatment_arms):
            row = main_row.copy()
            row['arm_number'] = i + 1
            
            for key, value in arm.items():
                if isinstance(value, (list, dict)):
                    row[f'arm_{key}'] = json.dumps(value, ensure_ascii=False)
                else:
                    row[f'arm_{key}'] = str(value) if value is not None else ''
            
            rows.append(row)
    
    # Write to CSV with proper encoding
    if rows:
        try:
            # Use UTF-8 with BOM for better Excel compatibility
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        except UnicodeEncodeError:
            # Fallback to UTF-8 without BOM if there are encoding issues
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    
    return len(rows)

def create_combined_csv(results: List[Dict[str, Any]], output_dir: str) -> str:
    """Create a combined CSV file with all successful results, preserving treatment arm structure"""
    if not results:
        return ""
    
    # Collect all successful data
    all_data = []
    for result in results:
        if result["status"] == "success":
            # Try to load the validated JSON data
            try:
                pdf_number = result["pdf_number"]
                timestamp = result.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
                
                # Find the validated JSON file for this PDF
                json_pattern = os.path.join(output_dir, f'validated_{pdf_number}.json')
                json_files = glob.glob(json_pattern)
                
                if json_files:
                    # Use the file (should be only one with simplified naming)
                    latest_json = json_files[0]
                    with open(latest_json, 'r', encoding='utf-8') as f:
                        validated_data = json.load(f)
                    
                    if "data" in validated_data and validated_data["data"]:
                        all_data.append(validated_data["data"])
            except Exception as e:
                print(f"⚠️  Warning: Could not load data for PDF {result.get('pdf_number', 'unknown')}: {str(e)}")
    
    if not all_data:
        print("⚠️  No valid data found for combined CSV")
        return ""
    
    # Create combined CSV
    combined_csv_file = os.path.join(output_dir, 'combined.csv')
    
    # Flatten all data into rows (same logic as save_to_csv)
    all_rows = []
    for data in all_data:
        # Handle main fields (non-treatment arm fields)
        main_row = {}
        treatment_arms = data.get('treatment_arms', [])
        
        # Add all non-treatment arm fields
        for key, value in data.items():
            if key != 'treatment_arms':
                if isinstance(value, (list, dict)):
                    main_row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    main_row[key] = str(value) if value is not None else ''
        
        # If no treatment arms, just save the main row
        if not treatment_arms:
            all_rows.append(main_row)
        else:
            # For each treatment arm, create a row with main data + arm data
            for i, arm in enumerate(treatment_arms):
                row = main_row.copy()
                row['arm_number'] = i + 1
                
                for key, value in arm.items():
                    if isinstance(value, (list, dict)):
                        row[f'arm_{key}'] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[f'arm_{key}'] = str(value) if value is not None else ''
                
                all_rows.append(row)
    
    if not all_rows:
        print("⚠️  No rows generated for combined CSV")
        return ""
    
    # Get all unique field names from all rows
    all_fields = set()
    for row in all_rows:
        all_fields.update(row.keys())
    
    # Sort fields for consistent ordering
    field_order = sorted(list(all_fields))
    
    # Write combined CSV
    with open(combined_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=field_order)
        writer.writeheader()
        
        for row in all_rows:
            # Ensure all fields are present (fill missing with empty string)
            complete_row = {field: row.get(field, '') for field in field_order}
            writer.writerow(complete_row)
    
    print(f"✅ Combined CSV created: {os.path.basename(combined_csv_file)} ({len(all_rows)} rows)")
    return combined_csv_file

def process_single_markdown(markdown_path: str, output_dir: str, client: OpenAIClient, 
                           enhanced_extractor: EnhancedClinicalExtractor, 
                           total_files: int, current_file: int) -> Dict[str, Any]:
    """Process a single Marker-enhanced markdown file with enhanced system and progress tracking"""
    
    # Extract PDF number from filename (e.g., "15.md" -> "15")
    markdown_filename = os.path.basename(markdown_path)
    pdf_number = markdown_filename.split('.')[0]  # Get the PDF number
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*80}")
    print(f"📄 Processing Markdown {current_file}/{total_files}: {markdown_filename}")
    print(f"   📊 Source PDF: {pdf_number}.pdf")
    print(f"{'='*80}")
    
    result = {
        "markdown_file": markdown_path,
        "pdf_number": pdf_number,
        "status": "failed",
        "error": None,
        "extraction_time": 0,
        "text_length": 0,
        "nct_number": None,
        "treatment_arms": 0,
        "rows_generated": 0
    }
    
    start_time = time.time()
    
    try:
        # Stage 1: Read markdown content
        print(f"🔄 [{current_file}/{total_files}] Reading markdown content from {markdown_filename}...")
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        except Exception as e:
            result["error"] = f"Could not read markdown file: {str(e)}"
            print(f"❌ [{current_file}/{total_files}] Markdown reading failed")
            return result
        
        if not full_text:
            result["error"] = "Markdown file is empty"
            print(f"❌ [{current_file}/{total_files}] Markdown file is empty")
            return result
        
        result["text_length"] = len(full_text)
        print(f"✅ [{current_file}/{total_files}] Markdown content loaded: {len(full_text):,} characters")
        
        # Stage 2: Pre-validation
        print(f"🔄 [{current_file}/{total_files}] Pre-validation...")
        can_process, validation_data = enhanced_extractor.pre_validate(full_text)
        
        if not can_process:
            result["error"] = f"Pre-validation failed: {validation_data.get('errors', [])}"
            print(f"❌ [{current_file}/{total_files}] Pre-validation failed")
            return result
        
        result["nct_number"] = validation_data.get("nct_number")
        result["treatment_arms"] = validation_data.get("treatment_arms_count", 0)
        print(f"✅ [{current_file}/{total_files}] Pre-validation passed: NCT={result['nct_number']}, Arms={result['treatment_arms']}")
        
        # Stage 3: Create focused prompt
        print(f"🔄 [{current_file}/{total_files}] Creating focused prompt...")
        focused_prompt = enhanced_extractor.create_focused_prompt(full_text, validation_data)
        print(f"✅ [{current_file}/{total_files}] Focused prompt created: {len(focused_prompt):,} characters")
        
        # Stage 4: LLM Processing with progress tracking
        print(f"🔄 [{current_file}/{total_files}] LLM Processing (this may take 1-2 minutes)...")
        print(f"   📊 Sending request to OpenAI API...")
        
        llm_start_time = time.time()
        raw_response = client.get_chat_completion([{"role": "user", "content": focused_prompt}])
        llm_end_time = time.time()
        
        if not raw_response:
            result["error"] = "LLM processing failed - no response received"
            print(f"❌ [{current_file}/{total_files}] LLM processing failed")
            return result
        
        llm_time = llm_end_time - llm_start_time
        print(f"✅ [{current_file}/{total_files}] LLM processing completed in {llm_time:.1f} seconds")
        
        # Stage 5: Parse and validate response
        print(f"🔄 [{current_file}/{total_files}] Parsing LLM response...")
        try:
            raw_json = json.loads(raw_response)
            print(f"✅ [{current_file}/{total_files}] JSON parsing successful")
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON response from LLM: {str(e)}"
            print(f"❌ [{current_file}/{total_files}] JSON parsing failed")
            return result
        
        # Stage 6: Post-processing validation
        print(f"🔄 [{current_file}/{total_files}] Post-processing validation...")
        validated_data = enhanced_extractor.validate_and_clean_data(raw_json, validation_data)
        
        # Add PDF number to the extracted data
        if "data" in validated_data and validated_data["data"]:
            validated_data["data"]["PDF number"] = f"{pdf_number}.pdf"
            validated_data["data"]["Source markdown"] = markdown_filename
            print(f"✅ [{current_file}/{total_files}] Added source info: PDF={pdf_number}.pdf, Markdown={markdown_filename}")
        
        # Stage 7: Save outputs
        print(f"🔄 [{current_file}/{total_files}] Saving outputs...")
        
        # Save validated JSON
        validated_json_file = os.path.join(output_dir, f'validated_{pdf_number}.json')
        with open(validated_json_file, 'w', encoding='utf-8') as f:
            json.dump(validated_data, f, indent=4, ensure_ascii=False)
        
        # Save validated CSV
        validated_csv_file = os.path.join(output_dir, f'validated_{pdf_number}.csv')
        rows_generated = save_to_csv(validated_data["data"], validated_csv_file)
        result["rows_generated"] = rows_generated
        
        # Save raw LLM response
        raw_json_file = os.path.join(output_dir, f'raw_llm_{pdf_number}.json')
        with open(raw_json_file, 'w', encoding='utf-8') as f:
            json.dump(raw_json, f, indent=4, ensure_ascii=False)
        
        print(f"✅ [{current_file}/{total_files}] Outputs saved:")
        print(f"   📄 JSON: {os.path.basename(validated_json_file)}")
        print(f"   📊 CSV: {os.path.basename(validated_csv_file)} ({rows_generated} rows)")
        print(f"   🔍 Raw LLM: {os.path.basename(raw_json_file)}")
        
        # Update result
        result["status"] = "success"
        result["extraction_time"] = time.time() - start_time
        
        print(f"✅ [{current_file}/{total_files}] Processing completed successfully!")
        print(f"   ⏱️  Total time: {result['extraction_time']:.1f} seconds")
        print(f"   📊 Validation: {validated_data['extraction_metadata']['validation_status']}")
        print(f"   ⚠️  Errors: {len(validated_data['extraction_metadata']['errors'])}")
        print(f"   ⚠️  Warnings: {len(validated_data['extraction_metadata']['warnings'])}")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        result["extraction_time"] = time.time() - start_time
        print(f"❌ [{current_file}/{total_files}] Processing failed: {str(e)}")
        return result

def main():
    """Main batch processing function"""
    
    # Setup
    markdown_dir = "input/marker_preprocessed"
    
    # Create sequential batch output directory
    base_output_dir = "output"
    batch_counter = 1
    while os.path.exists(os.path.join(base_output_dir, f"batch_output_{batch_counter}")):
        batch_counter += 1
    
    output_dir = os.path.join(base_output_dir, f"batch_output_{batch_counter}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all markdown files
    markdown_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    markdown_files.sort()  # Sort for consistent ordering
    
    if not markdown_files:
        print("❌ No Marker-enhanced markdown files found in input/marker_preprocessed directory")
        print("   Please run marker_enhanced_pipeline.py first to generate markdown files")
        return
    
    print(f"🚀 Enhanced Clinical Trial Data Extraction - Batch Processing")
    print(f"{'='*80}")
    print(f"📁 Markdown directory: {markdown_dir}")
    print(f"📁 Batch output directory: {output_dir}")
    print(f"📄 Found {len(markdown_files)} markdown files to process")
    print(f"{'='*80}")
    
    # Initialize components
    print("🔧 Initializing components...")
    client = OpenAIClient()
    enhanced_extractor = EnhancedClinicalExtractor()
    logger = get_logger(__name__)
    
    # Process each markdown file
    results = []
    total_files = len(markdown_files)
    
    for i, markdown_path in enumerate(markdown_files, 1):
        result = process_single_markdown(
            markdown_path, output_dir, client, enhanced_extractor, 
            total_files, i
        )
        results.append(result)
        
        # Brief pause between files
        if i < total_files:
            print(f"\n⏳ Waiting 2 seconds before next file...")
            time.sleep(2)
    
    # Generate summary report
    print(f"\n{'='*80}")
    print(f"📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total_files - successful
    total_time = sum(r["extraction_time"] for r in results)
    total_rows = sum(r["rows_generated"] for r in results if r["status"] == "success")
    
    # Get API usage summary
    api_usage = client.get_usage_summary()
    
    print(f"📄 Total files processed: {total_files}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total processing time: {total_time:.1f} seconds")
    print(f"📊 Total CSV rows generated: {total_rows}")
    print(f"\n💰 API USAGE SUMMARY:")
    print(f"   🔢 Total API requests: {api_usage['total_requests']}")
    print(f"   📝 Total prompt tokens: {api_usage['total_prompt_tokens']:,}")
    print(f"   💬 Total completion tokens: {api_usage['total_completion_tokens']:,}")
    print(f"   🎯 Total tokens: {api_usage['total_tokens']:,}")
    print(f"   💵 Total cost: ${api_usage['total_cost']:.6f}")
    
    # Print detailed API usage summary
    client.print_usage_summary()
    
    if failed > 0:
        print(f"\n❌ Failed files:")
        for result in results:
            if result["status"] == "failed":
                print(f"   - {os.path.basename(result['markdown_file'])}: {result['error']}")
    
    # Create combined CSV
    print(f"\n🔄 Creating combined CSV file...")
    combined_csv_file = create_combined_csv(results, output_dir)
    
    # Save batch summary
    summary_file = os.path.join(output_dir, 'batch_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "batch_metadata": {
                "processing_date": datetime.now().isoformat(),
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "total_time": total_time,
                "total_rows": total_rows,
                "combined_csv": combined_csv_file if combined_csv_file else None
            },
            "api_usage": api_usage,
            "results": results
        }, f, indent=4, ensure_ascii=False)
    
    print(f"\n📄 Batch summary saved to: {os.path.basename(summary_file)}")
    if combined_csv_file:
        print(f"📊 Combined CSV saved to: {os.path.basename(combined_csv_file)}")
    print(f"📁 All outputs saved to: {output_dir}")
    print(f"🎉 Batch processing completed!")

if __name__ == "__main__":
    main() 