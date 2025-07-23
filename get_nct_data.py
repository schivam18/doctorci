#!/usr/bin/env python3
"""
Get Comprehensive NCT Data from ClinicalTrials.gov API

Enhanced script to retrieve comprehensive data for specific NCT numbers and save to JSON files.
Retrieves detailed study information, results data, and all available fields.
"""

import sys
import os
from src.clinicaltrials_client import ClinicalTrialsAPIClient
from src.logger_config import setup_logging, get_logger

def read_nct_numbers_from_file(filename="nct_numbers.txt"):
    """
    Read NCT numbers from a text file.
    
    Args:
        filename: Name of the file containing NCT numbers
        
    Returns:
        List of NCT numbers
    """
    nct_numbers = []
    
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        print("Please create the file and add your NCT numbers (one per line).")
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Clean up the NCT number
                nct_id = line.strip()
                
                # Basic validation
                if nct_id.startswith('NCT') and len(nct_id) >= 11:
                    nct_numbers.append(nct_id)
                else:
                    print(f"Warning: Invalid NCT format on line {line_num}: {nct_id}")
        
        print(f"Read {len(nct_numbers)} valid NCT numbers from {filename}")
        return nct_numbers
        
    except Exception as e:
        print(f"Error reading file '{filename}': {str(e)}")
        return []

def get_comprehensive_nct_data(nct_numbers):
    """
    Get comprehensive data for specific NCT numbers and save to JSON.
    
    Args:
        nct_numbers: List of NCT numbers to retrieve
    """
    client = ClinicalTrialsAPIClient()
    
    print(f"Retrieving comprehensive data for {len(nct_numbers)} NCT number(s)...")
    print("=" * 60)
    
    results = {
        'timestamp': client.logger.info("Starting comprehensive NCT data retrieval"),
        'total_requested': len(nct_numbers),
        'successful': 0,
        'failed': 0,
        'studies': [],
        'errors': []
    }
    
    for i, nct_id in enumerate(nct_numbers, 1):
        print(f"\n[{i}/{len(nct_numbers)}] Processing: {nct_id}")
        
        try:
            is_valid, study_info = client.get_comprehensive_study_data(nct_id)
            
            if is_valid and study_info:
                results['successful'] += 1
                results['studies'].append({
                    'nct_id': nct_id,
                    'data': study_info
                })
                
                print(f"  ✓ Success: {study_info.brief_title[:60]}...")
                print(f"    Status: {study_info.overall_status}")
                print(f"    Phase: {', '.join(study_info.phase) if study_info.phase else 'N/A'}")
                print(f"    Sponsor: {study_info.lead_sponsor.get('name', 'N/A')}")
                print(f"    Enrollment: {study_info.enrollment_count or 'N/A'}")
                print(f"    Locations: {len(study_info.locations)} sites")
                print(f"    Has Results: {'Yes' if study_info.has_results else 'No'}")
                
            else:
                results['failed'] += 1
                results['errors'].append({
                    'nct_id': nct_id,
                    'error': 'Invalid or not found'
                })
                print(f"  ✗ Failed: Invalid or not found")
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'nct_id': nct_id,
                'error': str(e)
            })
            print(f"  ✗ Error: {str(e)}")
    
    # Save results to JSON
    if results['studies']:
        # Save individual comprehensive study files
        for study in results['studies']:
            nct_id = study['nct_id']
            filename = f"comprehensive_{nct_id}.json"
            client.save_to_json(study['data'], filename)
            print(f"\n  Comprehensive data saved to: {filename}")
        
        # Save combined results
        combined_filename = f"comprehensive_combined_{len(nct_numbers)}_studies.json"
        client.save_to_json(results, combined_filename)
        print(f"\n  Combined comprehensive results saved to: {combined_filename}")
    
    # Print detailed summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE DATA SUMMARY")
    print("=" * 60)
    print(f"Total requested: {results['total_requested']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['successful']/results['total_requested']*100:.1f}%")
    
    if results['studies']:
        print(f"\nRetrieved comprehensive data for:")
        for study in results['studies']:
            nct_id = study['nct_id']
            data = study['data']
            title = data.brief_title
            phase = ', '.join(data.phase) if data.phase else 'N/A'
            enrollment = data.enrollment_count or 'N/A'
            results_available = 'Yes' if data.has_results else 'No'
            print(f"  {nct_id}: {title[:40]}...")
            print(f"    Phase: {phase}, Enrollment: {enrollment}, Results: {results_available}")
    
    return results

def main():
    """Main function to read NCT numbers from file and process them."""
    setup_logging()
    logger = get_logger(__name__)
    
    print("ClinicalTrials.gov Comprehensive NCT Data Retrieval")
    print("=" * 60)
    print("Reading NCT numbers from nct_numbers.txt...")
    print("This will retrieve ALL available data including:")
    print("  • Study design and protocols")
    print("  • Eligibility criteria and outcomes")
    print("  • Sponsor and location information")
    print("  • Results data (if available)")
    print("  • Publications and references")
    print()
    
    try:
        # Read NCT numbers from file
        nct_numbers = read_nct_numbers_from_file()
        
        if not nct_numbers:
            print("No valid NCT numbers found. Please check your nct_numbers.txt file.")
            print("\nFile format should be:")
            print("NCT04380701")
            print("NCT04269498")
            print("NCT01234567")
            return
        
        print(f"Found {len(nct_numbers)} NCT numbers to process:")
        for i, nct_id in enumerate(nct_numbers, 1):
            print(f"  {i}. {nct_id}")
        
        # Confirm with user
        response = input(f"\nProceed with comprehensive data retrieval for {len(nct_numbers)} NCT numbers? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return
        
        # Get the comprehensive data
        results = get_comprehensive_nct_data(nct_numbers)
        
        print("\n" + "=" * 60)
        print("Comprehensive data retrieval complete!")
        print("Check the 'output' directory for detailed JSON files.")
        print("Each file contains extensive study information including:")
        print("  • Complete study protocols and design")
        print("  • Detailed eligibility criteria")
        print("  • Primary/secondary outcomes")
        print("  • Sponsor and collaborator information")
        print("  • Study locations and contacts")
        print("  • Results data and adverse events (if available)")
        print("  • Publications and references")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 