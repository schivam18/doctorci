#!/usr/bin/env python3
"""
Enhanced batch processing script for clinical trial data extraction system.
Processes all Marker-enhanced markdown files with unified extraction pipeline.
Uses the improved OpenAI client with integrated EnhancedClinicalExtractor.
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

from openai_client import OpenAIClient
from logger_config import get_logger


def save_to_csv(data: Dict[str, Any], output_file: str) -> int:
    """Save data to CSV format with proper encoding and treatment arm handling"""
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
    """Create a combined CSV file with all successful results"""
    if not results:
        return ""
    
    # Collect all successful data
    all_data = []
    for result in results:
        if result["status"] == "success":
            try:
                pdf_number = result["pdf_number"]
                
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
                    elif isinstance(validated_data, dict) and validated_data.get("NCT Number"):
                        # Handle case where data is at root level
                        all_data.append(validated_data)
            except Exception as e:
                print(f"⚠️  Warning: Could not load data for PDF {result.get('pdf_number', 'unknown')}: {str(e)}")
    
    if not all_data:
        print("⚠️  No valid data found for combined CSV")
        return ""
    
    # Create combined CSV
    combined_csv_file = os.path.join(output_dir, 'combined_results.csv')
    
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
    
    # Sort fields for consistent ordering (prioritize important fields)
    priority_fields = [
        'NCT Number', 'Publication Name', 'Publication Year', 'Trial name', 
        'Cancer Type', 'Clinical Trial Phase', 'arm_number', 'arm_Generic name',
        'arm_Number of patients', 'arm_Line of Treatment'
    ]
    
    other_fields = sorted([f for f in all_fields if f not in priority_fields])
    field_order = [f for f in priority_fields if f in all_fields] + other_fields
    
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
                           total_files: int, current_file: int) -> Dict[str, Any]:
    """Process a single markdown file using the enhanced unified extraction pipeline"""
    
    # Extract PDF number from filename (e.g., "15.md" -> "15")
    markdown_filename = os.path.basename(markdown_path)
    pdf_number = markdown_filename.split('.')[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*80}")
    print(f"📄 Processing Markdown {current_file}/{total_files}: {markdown_filename}")
    print(f"   📊 Source PDF: {pdf_number}.pdf")
    print(f"   🚀 Using Enhanced Unified Pipeline")
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
        "rows_generated": 0,
        "timestamp": timestamp
    }
    
    start_time = time.time()
    
    try:
        # Stage 1: Read markdown content
        print(f"🔄 [{current_file}/{total_files}] Reading markdown content...")
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
        print(f"✅ [{current_file}/{total_files}] Markdown loaded: {len(full_text):,} characters")
        
        # Stage 2: Enhanced unified extraction using improved OpenAI client
        print(f"🔄 [{current_file}/{total_files}] Enhanced unified extraction processing...")
        print(f"   📊 Using integrated EnhancedClinicalExtractor")
        print(f"   🎯 Enhanced prompts with NA/empty protocol")
        print(f"   ✅ Three-stage validation pipeline")
        
        extraction_start_time = time.time()
        extracted_data = client.extract_publication_data(full_text)
        extraction_end_time = time.time()
        
        if not extracted_data:
            result["error"] = "Enhanced unified extraction failed"
            print(f"❌ [{current_file}/{total_files}] Enhanced extraction failed")
            return result
        
        extraction_time = extraction_end_time - extraction_start_time
        print(f"✅ [{current_file}/{total_files}] Enhanced extraction completed in {extraction_time:.1f} seconds")
        
        # Stage 3: Extract metadata from results
        result["nct_number"] = extracted_data.get("NCT Number")
        treatment_arms = extracted_data.get("treatment_arms", [])
        result["treatment_arms"] = len(treatment_arms)
        
        print(f"📊 [{current_file}/{total_files}] Extraction results:")
        print(f"   🔢 NCT Number: {result['nct_number']}")
        print(f"   💊 Treatment Arms: {result['treatment_arms']}")
        
        # Stage 4: Add source metadata
        extracted_data["PDF number"] = f"{pdf_number}.pdf"
        extracted_data["Source markdown"] = markdown_filename
        extracted_data["Processing timestamp"] = timestamp
        
        # Stage 5: Quality validation using client's built-in method
        quality_metrics = client.validate_extraction_quality(extracted_data)
        print(f"   📈 Quality Score: {quality_metrics['quality_score']}/100")
        print(f"   ✅ Completeness: {quality_metrics['completeness']*100:.1f}%")
        
        if quality_metrics['issues']:
            print(f"   ⚠️  Quality Issues: {len(quality_metrics['issues'])}")
            for issue in quality_metrics['issues'][:3]:  # Show first 3 issues
                print(f"      - {issue}")
        
        # Stage 6: Save outputs
        print(f"🔄 [{current_file}/{total_files}] Saving outputs...")
        
        # Create validation metadata structure for compatibility
        validation_metadata = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "validation_status": "validated",
                "errors": quality_metrics.get('issues', []),
                "warnings": quality_metrics.get('warnings', []),
                "quality_score": quality_metrics['quality_score'],
                "completeness": quality_metrics['completeness'],
                "extraction_method": "enhanced_unified_pipeline",
                "prompt_version": "enhanced_2.1"
            },
            "data": extracted_data
        }
        
        # Save validated JSON
        validated_json_file = os.path.join(output_dir, f'validated_{pdf_number}.json')
        with open(validated_json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_metadata, f, indent=4, ensure_ascii=False)
        
        # Save validated CSV
        validated_csv_file = os.path.join(output_dir, f'validated_{pdf_number}.csv')
        rows_generated = save_to_csv(extracted_data, validated_csv_file)
        result["rows_generated"] = rows_generated
        
        print(f"✅ [{current_file}/{total_files}] Outputs saved:")
        print(f"   📄 JSON: {os.path.basename(validated_json_file)}")
        print(f"   📊 CSV: {os.path.basename(validated_csv_file)} ({rows_generated} rows)")
        
        # Update result
        result["status"] = "success"
        result["extraction_time"] = time.time() - start_time
        
        print(f"✅ [{current_file}/{total_files}] Processing completed successfully!")
        print(f"   ⏱️  Total time: {result['extraction_time']:.1f} seconds")
        print(f"   🎯 Quality: {quality_metrics['quality_score']}/100")
        print(f"   📊 Completeness: {quality_metrics['completeness']*100:.1f}%")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        result["extraction_time"] = time.time() - start_time
        print(f"❌ [{current_file}/{total_files}] Processing failed: {str(e)}")
        return result


def main():
    """Main batch processing function with enhanced unified pipeline"""
    
    # Setup
    markdown_dir = "input/marker_preprocessed"
    
    # Create sequential batch output directory
    base_output_dir = "output"
    batch_counter = 1
    while os.path.exists(os.path.join(base_output_dir, f"batch_enhanced_output_{batch_counter}")):
        batch_counter += 1
    
    output_dir = os.path.join(base_output_dir, f"batch_enhanced_output_{batch_counter}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all markdown files
    markdown_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    markdown_files.sort()  # Sort for consistent ordering
    
    if not markdown_files:
        print("❌ No Marker-enhanced markdown files found in input/marker_preprocessed directory")
        print("   Please run marker_enhanced_pipeline.py first to generate markdown files")
        return
    
    print(f"🚀 Enhanced Clinical Trial Data Extraction - Unified Batch Processing")
    print(f"{'='*80}")
    print(f"📁 Markdown directory: {markdown_dir}")
    print(f"📁 Batch output directory: {output_dir}")
    print(f"📄 Found {len(markdown_files)} markdown files to process")
    print(f"🔧 Using Enhanced Unified Pipeline:")
    print(f"   ✅ Integrated EnhancedClinicalExtractor")
    print(f"   ✅ Improved prompts with NA/empty protocol")
    print(f"   ✅ Three-stage validation (Pre → Extract → Post)")
    print(f"   ✅ Controlled vocabulary validation")
    print(f"   ✅ Enhanced quality metrics")
    print(f"{'='*80}")
    
    # Initialize enhanced client
    print("🔧 Initializing enhanced components...")
    client = OpenAIClient()  # Now includes integrated EnhancedClinicalExtractor
    logger = get_logger(__name__)
    
    print("✅ Enhanced OpenAI client initialized with unified extraction pipeline")
    
    # Process each markdown file
    results = []
    total_files = len(markdown_files)
    
    for i, markdown_path in enumerate(markdown_files, 1):
        result = process_single_markdown(
            markdown_path, output_dir, client, total_files, i
        )
        results.append(result)
        
        # Brief pause between files to prevent rate limiting
        if i < total_files:
            print(f"\n⏳ Waiting 2 seconds before next file...")
            time.sleep(2)
    
    # Generate comprehensive summary report
    print(f"\n{'='*80}")
    print(f"📊 ENHANCED BATCH PROCESSING SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total_files - successful
    total_time = sum(r["extraction_time"] for r in results)
    total_rows = sum(r["rows_generated"] for r in results if r["status"] == "success")
    
    # Get comprehensive API usage summary
    api_usage = client.get_usage_summary()
    
    print(f"📄 Total files processed: {total_files}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total processing time: {total_time:.1f} seconds")
    print(f"📊 Total CSV rows generated: {total_rows}")
    print(f"🎯 Success rate: {(successful/total_files)*100:.1f}%")
    
    print(f"\n💰 ENHANCED API USAGE SUMMARY:")
    print(f"   🔢 Total API requests: {api_usage['total_requests']}")
    print(f"   📝 Total prompt tokens: {api_usage['total_prompt_tokens']:,}")
    print(f"   💬 Total completion tokens: {api_usage['total_completion_tokens']:,}")
    print(f"   🎯 Total tokens: {api_usage['total_tokens']:,}")
    print(f"   💵 Total cost: ${api_usage['total_cost']:.6f}")
    print(f"   🤖 Model: {api_usage['model_used']}")
    print(f"   ⚙️  Method: {api_usage['extraction_method']}")
    
    # Print enhanced usage summary
    client.print_usage_summary()
    
    # Quality metrics summary
    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        avg_quality = sum(r.get("quality_score", 0) for r in successful_results) / len(successful_results)
        avg_completeness = sum(r.get("completeness", 0) for r in successful_results) / len(successful_results)
        print(f"\n📈 QUALITY METRICS:")
        print(f"   🎯 Average Quality Score: {avg_quality:.1f}/100")
        print(f"   ✅ Average Completeness: {avg_completeness*100:.1f}%")
    
    if failed > 0:
        print(f"\n❌ Failed files:")
        for result in results:
            if result["status"] == "failed":
                print(f"   - {os.path.basename(result['markdown_file'])}: {result['error']}")
    
    # Create enhanced combined CSV
    print(f"\n🔄 Creating enhanced combined CSV file...")
    combined_csv_file = create_combined_csv(results, output_dir)
    
    # Save comprehensive batch summary
    summary_file = os.path.join(output_dir, 'enhanced_batch_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "batch_metadata": {
                "processing_date": datetime.now().isoformat(),
                "pipeline_version": "enhanced_unified_2.1",
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful/total_files)*100,
                "total_time": total_time,
                "total_rows": total_rows,
                "combined_csv": combined_csv_file if combined_csv_file else None
            },
            "api_usage": api_usage,
            "quality_metrics": {
                "average_quality_score": sum(r.get("quality_score", 0) for r in successful_results) / len(successful_results) if successful_results else 0,
                "average_completeness": sum(r.get("completeness", 0) for r in successful_results) / len(successful_results) if successful_results else 0
            },
            "extraction_method": "enhanced_unified_pipeline",
            "results": results
        }, f, indent=4, ensure_ascii=False)
    
    print(f"\n📄 Enhanced batch summary saved to: {os.path.basename(summary_file)}")
    if combined_csv_file:
        print(f"📊 Enhanced combined CSV saved to: {os.path.basename(combined_csv_file)}")
    print(f"📁 All outputs saved to: {output_dir}")
    print(f"🎉 Enhanced batch processing completed with unified pipeline!")
    
    # Final statistics
    print(f"\n🏆 FINAL STATISTICS:")
    print(f"   📈 Pipeline Version: Enhanced Unified 2.1")
    print(f"   ⚡ Processing Speed: {total_time/total_files:.1f} seconds per file")
    print(f"   💎 Data Quality: Enhanced validation with NA/empty protocol")
    print(f"   🎯 Success Rate: {(successful/total_files)*100:.1f}%")


if __name__ == "__main__":
    main()
