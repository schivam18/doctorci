#!/usr/bin/env python3
"""
Compare comprehensive extraction results with original 26.txt file
"""

import json
import os
from typing import Dict, Any, List

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}

def parse_original_txt(file_path: str) -> Dict[str, Any]:
    """Parse the original 26.txt file into structured data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the structured format
        data = {}
        current_arm = None
        
        lines = content.split('\n')
        for line in lines:
            if line.strip() == '':
                continue
                
            if line.startswith('Treatment Arm'):
                current_arm = line.split(':')[0].strip()
                data[current_arm] = {}
                continue
                
            if '\t' in line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip()
                    value = value.strip()
                    
                    if current_arm:
                        data[current_arm][key] = value
                    else:
                        data[key] = value
        
        return data
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")
        return {}

def compare_field_values(new_data: Dict, old_data: Dict, field_name: str) -> Dict[str, Any]:
    """Compare a specific field between new and original data"""
    new_value = new_data.get(field_name, "")
    old_value = old_data.get(field_name, "")
    
    if new_value == old_value:
        return {"status": "✅ Match", "new": new_value, "old": old_value}
    elif new_value and not old_value:
        return {"status": "🆕 New", "new": new_value, "old": old_value}
    elif old_value and not new_value:
        return {"status": "❌ Missing", "new": new_value, "old": old_value}
    else:
        return {"status": "🔄 Different", "new": new_value, "old": old_value}

def compare_arm_data(new_arm: Dict, old_arm: Dict, arm_name: str) -> Dict[str, Any]:
    """Compare treatment arm data"""
    comparison = {
        "arm_name": arm_name,
        "fields": {}
    }
    
    # Key fields to compare
    key_fields = [
        "Number of patients", "Objective response rate (ORR)", "Complete Response (CR)",
        "Median Progression free survival (PFS)", "p-value of median PFS", "Hazard ratio (HR) PFS",
        "Adverse events (AE)", "Grade 3+ or Grade 3 higher TRAE", "AE leading to discontinuation"
    ]
    
    for field in key_fields:
        comparison["fields"][field] = compare_field_values(new_arm, old_arm, field)
    
    return comparison

def main():
    print("🔍 COMPARING WITH ORIGINAL 26.TXT")
    print("=" * 60)
    
    # Load files
    new_file = "test_output/test_comprehensive_26.json"
    original_file = "26.txt"
    
    new_data = load_json_file(new_file)
    original_data = parse_original_txt(original_file)
    
    if not new_data or not original_data:
        print("❌ Failed to load comparison files")
        return
    
    # Extract the main data
    new_extraction = new_data.get("extraction_result", {})
    new_arms = new_extraction.get("treatment_arms", [])
    
    print(f"📄 New extraction: {new_file}")
    print(f"📄 Original data: {original_file}")
    print()
    
    # Compare key publication fields
    key_fields = [
        "Publication Name", "Publication Year", "NCT Number", 
        "Clinical Trial Phase", "Sponsors", "Cancer Type"
    ]
    
    print("🔑 PUBLICATION FIELD COMPARISON:")
    print("-" * 40)
    for field in key_fields:
        comparison = compare_field_values(new_extraction, original_data, field)
        status_icon = comparison["status"].split()[0]
        print(f"{status_icon} {field}:")
        print(f"   New:  {comparison['new']}")
        print(f"   Orig: {comparison['old']}")
        print()
    
    # Compare treatment arms
    print("💊 TREATMENT ARM COMPARISON:")
    print("-" * 40)
    
    # Map original arm data
    original_arms = {}
    for key, value in original_data.items():
        if key.startswith("Treatment Arm"):
            original_arms[key] = value
    
    print(f"Arm Count: New {len(new_arms)} vs Original {len(original_arms)}")
    print()
    
    # Compare each arm
    for i, new_arm in enumerate(new_arms):
        arm_name = f"Treatment Arm {i+1}"
        original_arm = original_arms.get(arm_name, {})
        
        print(f"📊 {arm_name}:")
        arm_comparison = compare_arm_data(new_arm, original_arm, arm_name)
        
        for field, comp in arm_comparison["fields"].items():
            status_icon = comp["status"].split()[0]
            print(f"  {status_icon} {field}:")
            print(f"    New:  {comp['new']}")
            print(f"    Orig: {comp['old']}")
        print()
    
    # Summary statistics
    print("📊 ACCURACY SUMMARY:")
    print("-" * 40)
    
    total_fields = 0
    matches = 0
    improvements = 0
    regressions = 0
    
    # Count publication field accuracy
    for field in key_fields:
        comparison = compare_field_values(new_extraction, original_data, field)
        total_fields += 1
        if "Match" in comparison["status"]:
            matches += 1
        elif "New" in comparison["status"]:
            improvements += 1
        elif "Different" in comparison["status"]:
            regressions += 1
    
    # Count arm field accuracy
    for i, new_arm in enumerate(new_arms):
        arm_name = f"Treatment Arm {i+1}"
        original_arm = original_arms.get(arm_name, {})
        
        key_arm_fields = [
            "Number of patients", "Objective response rate (ORR)", 
            "Complete Response (CR)", "Adverse events (AE)"
        ]
        
        for field in key_arm_fields:
            comparison = compare_field_values(new_arm, original_arm, field)
            total_fields += 1
            if "Match" in comparison["status"]:
                matches += 1
            elif "New" in comparison["status"]:
                improvements += 1
            elif "Different" in comparison["status"]:
                regressions += 1
    
    accuracy = (matches / total_fields * 100) if total_fields > 0 else 0
    
    print(f"📈 Overall Accuracy: {accuracy:.1f}%")
    print(f"✅ Exact Matches: {matches}/{total_fields}")
    print(f"🆕 New Fields: {improvements}")
    print(f"🔄 Differences: {regressions}")
    
    # Key findings
    print("\n🎯 KEY FINDINGS:")
    print("-" * 40)
    
    # Check specific critical fields
    critical_fields = [
        ("Publication Name", new_extraction, original_data),
        ("NCT Number", new_extraction, original_data),
        ("Cancer Type", new_extraction, original_data)
    ]
    
    for field_name, new_data, orig_data in critical_fields:
        new_val = new_data.get(field_name, "")
        orig_val = orig_data.get(field_name, "")
        if new_val == orig_val:
            print(f"✅ {field_name}: Perfect match")
        elif new_val and not orig_val:
            print(f"🆕 {field_name}: New extraction")
        elif orig_val and not new_val:
            print(f"❌ {field_name}: Missing in extraction")
        else:
            print(f"🔄 {field_name}: Different values")
    
    # Check arm-specific data
    if new_arms and original_arms:
        first_arm_key = list(original_arms.keys())[0]
        orig_arm = original_arms[first_arm_key]
        new_arm = new_arms[0]
        
        print(f"\n💊 Arm 1 Key Metrics:")
        for field in ["Number of patients", "Objective response rate (ORR)", "Adverse events (AE)"]:
            new_val = new_arm.get(field, "")
            orig_val = orig_arm.get(field, "")
            if new_val == orig_val:
                print(f"  ✅ {field}: {new_val}")
            else:
                print(f"  🔄 {field}: New={new_val}, Orig={orig_val}")

if __name__ == "__main__":
    main()