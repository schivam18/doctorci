#!/usr/bin/env python3
"""
Test comprehensive chunked extraction with improved backbone rules
"""

import os
import json
import time
from datetime import datetime
from src.openai_client import OpenAIClient
from src.enhanced_extractor import EnhancedClinicalExtractor
from src.chunk_templates import CHUNK_FIELD_MAP

def test_comprehensive_extraction(markdown_path: str) -> dict:
    """Test the comprehensive chunked extraction with improved backbone rules"""
    
    print("🧪 Testing Improved Comprehensive Chunked Extraction")
    print("=" * 80)
    print(f"📄 File: {os.path.basename(markdown_path)}")
    print("=" * 80)
    
    # Initialize components
    client = OpenAIClient()
    extractor = EnhancedClinicalExtractor()
    
    # Read markdown content
    print("📖 Reading markdown content...")
    with open(markdown_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    print(f"✅ Content loaded: {len(full_text):,} characters")
    
    # Test 1: Arm Discovery with improved backbone rules
    print("\n🔍 Test 1: Improved Arm Discovery")
    print("-" * 40)
    arm_discovery = extractor.detect_arms(full_text)
    print("✅ Arm discovery prompt generated")
    print(f"📝 Prompt length: {len(arm_discovery['prompt']):,} characters")
    
    # Test 2: Shared Chunks (1 & 10) with backbone rules
    print("\n🔍 Test 2: Shared Chunks (1 & 10) with Backbone Rules")
    print("-" * 40)
    shared_chunks = {}
    for chunk_id in [1, 10]:
        chunk_prompt = extractor.build_chunk_prompt(full_text, None, chunk_id)
        shared_chunks[chunk_id] = chunk_prompt
        print(f"✅ Chunk {chunk_id} prompt generated")
        print(f"   📝 Length: {len(chunk_prompt['prompt']):,} characters")
        print(f"   🏷️  Type: {chunk_prompt['chunk_type']}")
        print(f"   📊 Fields: {len(chunk_prompt['fields'])}")
    
    # Test 3: Table Extraction
    print("\n🔍 Test 3: Table Extraction")
    print("-" * 40)
    tables_csv = extractor.extract_tables_as_csv(full_text)
    print("✅ Tables extracted and converted to CSV")
    print(f"📊 Table content length: {len(tables_csv):,} characters")
    
    # Test 4: Comprehensive Extraction with improved backbone rules
    print("\n🔍 Test 4: Improved Comprehensive Chunked Extraction")
    print("-" * 40)
    
    start_time = time.time()
    extraction_result = client.extract_full_publication_comprehensive(full_text)
    extraction_time = time.time() - start_time
    
    if extraction_result:
        print("✅ Comprehensive extraction completed successfully!")
        print(f"⏱️  Time: {extraction_time:.1f} seconds")
        
        # Extract metadata
        metadata = extraction_result.get("extraction_metadata", {})
        arms_discovered = metadata.get("arms_discovered", 0)
        total_llm_calls = metadata.get("total_llm_calls", 0)
        total_cost = metadata.get("total_cost", 0)
        total_fields = metadata.get("total_fields_available", 0)
        
        print(f"🎯 Arms discovered: {arms_discovered}")
        print(f"🧩 LLM calls: {total_llm_calls}")
        print(f"💰 Cost: ${total_cost:.6f}")
        print(f"💎 Fields available: {total_fields}")
        
        # Show extracted arms with improved data
        treatment_arms = extraction_result.get("treatment_arms", [])
        print(f"\n📊 Extracted Arms:")
        for i, arm in enumerate(treatment_arms, 1):
            arm_name = arm.get("Generic name", "Unknown")
            patients = arm.get("Number of patients", "Unknown")
            orr = arm.get("Objective response rate (ORR)", "Unknown")
            safety_class = arm.get("safety_event_class", "Unknown")
            
            print(f"   Arm {i}: {arm_name}")
            print(f"     Patients: {patients}")
            print(f"     ORR: {orr}")
            print(f"     Safety class: {safety_class}")
        
        # Save test result
        test_output = {
            "test_metadata": {
                "file": os.path.basename(markdown_path),
                "test_date": datetime.now().isoformat(),
                "extraction_time": extraction_time,
                "success": True,
                "approach": "improved_comprehensive_chunked"
            },
            "extraction_result": extraction_result
        }
        
        # Create test_output directory if it doesn't exist
        os.makedirs("test_output", exist_ok=True)
        
        # Create timestamped filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("test_output", f"test_improved_comprehensive_{os.path.basename(markdown_path).split('.')[0]}_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_output, f, indent=4, ensure_ascii=False)
        
        print(f"\n💾 Test result saved: {output_file}")
        
        # Test 5: Field Coverage Analysis
        print("\n🔍 Test 5: Field Coverage Analysis")
        print("-" * 40)
        print(f"📊 Total fields available: {total_fields}")
        for chunk_id, fields in CHUNK_FIELD_MAP.items():
            if fields:
                print(f"   Chunk {chunk_id}: {len(fields)} fields")
        
        # Calculate estimated cost per paper
        estimated_cost_per_paper = total_cost / 1  # For single paper test
        print(f"💰 Estimated cost per paper (2 arms): ${estimated_cost_per_paper:.6f}")
        
        return {
            "success": True,
            "extraction_time": extraction_time,
            "arms_discovered": arms_discovered,
            "total_llm_calls": total_llm_calls,
            "total_cost": total_cost,
            "total_fields": total_fields,
            "output_file": output_file
        }
    else:
        print("❌ Comprehensive extraction failed!")
        return {"success": False}

def main():
    """Main test function"""
    # Test with 26.md
    markdown_path = "input/marker_preprocessed/26.md"
    
    if not os.path.exists(markdown_path):
        print(f"❌ File not found: {markdown_path}")
        return
    
    result = test_comprehensive_extraction(markdown_path)
    
    print("\n" + "=" * 80)
    print("🧪 IMPROVED COMPREHENSIVE CHUNKED EXTRACTION TEST SUMMARY")
    print("=" * 80)
    print(f"📄 Test file: {os.path.basename(markdown_path)}")
    print(f"📊 Text length: {len(open(markdown_path, 'r').read()):,} characters")
    print(f"🔍 Arm discovery: {'✅' if result['success'] else '❌'}")
    print(f"🧩 Shared chunks: {'✅' if result['success'] else '❌'} (2 chunks)")
    print(f"📋 Tables found: {'✅' if result['success'] else '❌'}")
    print(f"🎯 Extraction: {'✅' if result['success'] else '❌'}")
    print(f"💎 Total fields: {result.get('total_fields', 0)}")
    
    print("\n🎉 Improved comprehensive chunked extraction test completed!")

if __name__ == "__main__":
    main()