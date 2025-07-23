"""
ClinicalTrials.gov API Client - Enhanced Version

Enhanced client for retrieving comprehensive data from ClinicalTrials.gov API v2.
Retrieves detailed study information, results data, and all available fields.

Features:
- Rate limiting and retry logic
- Response caching to minimize API calls
- JSON file output for testing
- Comprehensive data extraction
- Basic error handling
"""

import json
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.logger_config import get_logger

@dataclass
class ComprehensiveStudyInfo:
    """Comprehensive study information from ClinicalTrials.gov"""
    # Basic Information
    nct_id: str
    brief_title: str
    official_title: str
    overall_status: str
    phase: List[str]
    study_type: str
    
    # Dates
    primary_completion_date: Optional[str]
    start_date: Optional[str]
    completion_date: Optional[str]
    first_posted_date: Optional[str]
    last_update_date: str
    
    # Study Design
    allocation: Optional[str]
    intervention_model: Optional[str]
    masking: Optional[str]
    primary_purpose: Optional[str]
    
    # Participants
    enrollment_count: Optional[int]
    enrollment_type: Optional[str]
    eligibility_criteria: Optional[str]
    healthy_volunteers: Optional[str]
    gender: Optional[str]
    minimum_age: Optional[str]
    maximum_age: Optional[str]
    
    # Conditions and Interventions
    conditions: List[str]
    interventions: List[Dict[str, str]]
    keywords: List[str]
    
    # Outcomes
    primary_outcomes: List[Dict[str, str]]
    secondary_outcomes: List[Dict[str, str]]
    other_outcomes: List[Dict[str, str]]
    
    # Sponsors and Collaborators
    lead_sponsor: Dict[str, str]
    collaborators: List[Dict[str, str]]
    
    # Locations
    locations: List[Dict[str, str]]
    
    # Contact Information
    overall_officials: List[Dict[str, str]]
    central_contacts: List[Dict[str, str]]
    
    # Publications and References
    references: List[Dict[str, str]]
    results_references: List[Dict[str, str]]
    
    # Results Data (if available)
    has_results: bool
    results_first_posted_date: Optional[str]
    participant_flow: Optional[Dict]
    baseline_characteristics: Optional[Dict]
    outcome_measures: Optional[Dict]
    adverse_events: Optional[Dict]
    
    # Additional Information
    brief_summary: Optional[str]
    detailed_description: Optional[str]
    study_docs: List[Dict[str, str]]

class ClinicalTrialsAPIClient:
    """
    Enhanced ClinicalTrials.gov API client for comprehensive data retrieval.
    """
    
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    def __init__(self, cache_duration_hours: int = 24, rate_limit_delay: float = 0.5):
        """
        Initialize the API client with caching and rate limiting.
        
        Args:
            cache_duration_hours: How long to cache API responses (default 24 hours)
            rate_limit_delay: Delay between API requests in seconds (default 0.5s)
        """
        self.logger = get_logger(__name__)
        self.cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info("Enhanced ClinicalTrials.gov API client initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve data from cache if valid."""
        if self._is_cache_valid(cache_key):
            self.logger.debug(f"Cache hit for key: {cache_key}")
            return self.cache[cache_key]['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Store data in cache with timestamp."""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        self.logger.debug(f"Cached data for key: {cache_key}")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request with rate limiting, retry, and error handling.
        
        Args:
            endpoint: API endpoint (e.g., '/studies')
            params: Query parameters
            
        Returns:
            API response as dictionary or None if failed
        """
        url = f"{self.BASE_URL}{endpoint}"
        cache_key = f"{endpoint}_{hash(str(sorted((params or {}).items())))}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Rate limiting
        self._rate_limit()
        
        try:
            self.logger.debug(f"Making API request to: {url}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self._set_cache(cache_key, data)
            
            self.logger.info(f"API request successful: {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
    
    def _safe_get(self, data: Dict, *keys, default=None):
        """Safely get nested dictionary values."""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def _extract_date(self, date_struct: Dict) -> Optional[str]:
        """Extract date from ClinicalTrials.gov date structure."""
        if not date_struct:
            return None
        return date_struct.get('date') or date_struct.get('text')
    
    def get_comprehensive_study_data(self, nct_id: str) -> Tuple[bool, Optional[ComprehensiveStudyInfo]]:
        """
        Get comprehensive study information including all available data.
        
        Args:
            nct_id: NCT number to retrieve (e.g., "NCT01234567")
            
        Returns:
            Tuple of (is_valid, comprehensive_study_info)
        """
        if not nct_id or not nct_id.startswith('NCT'):
            return False, None
        
        try:
            # Get full study data
            data = self._make_request(f"/studies/{nct_id}")
            if not data:
                return False, None
            
            protocol = data.get('protocolSection', {})
            results = data.get('resultsSection', {})
            derived = data.get('derivedSection', {})
            
            # Extract all sections
            identification = protocol.get('identificationModule', {})
            status = protocol.get('statusModule', {})
            design = protocol.get('designModule', {})
            arms_interventions = protocol.get('armsInterventionsModule', {})
            outcomes = protocol.get('outcomesModule', {})
            eligibility = protocol.get('eligibilityModule', {})
            contacts_locations = protocol.get('contactsLocationsModule', {})
            references = protocol.get('referencesModule', {})
            description = protocol.get('descriptionModule', {})
            conditions = protocol.get('conditionsModule', {})
            sponsor_collaborators = protocol.get('sponsorCollaboratorsModule', {})
            ipdsharing = protocol.get('ipdSharingStatementModule', {})
            
            # Build comprehensive study info
            comprehensive_info = ComprehensiveStudyInfo(
                # Basic Information
                nct_id=identification.get('nctId', nct_id),
                brief_title=identification.get('briefTitle', ''),
                official_title=identification.get('officialTitle', ''),
                overall_status=status.get('overallStatus', ''),
                phase=design.get('phases', []),
                study_type=design.get('studyType', ''),
                
                # Dates
                primary_completion_date=self._extract_date(status.get('primaryCompletionDateStruct')),
                start_date=self._extract_date(status.get('startDateStruct')),
                completion_date=self._extract_date(status.get('completionDateStruct')),
                first_posted_date=self._extract_date(status.get('studyFirstPostDateStruct')),
                last_update_date=status.get('lastUpdatePostDate', ''),
                
                # Study Design
                allocation=self._safe_get(design, 'designInfo', 'allocation'),
                intervention_model=self._safe_get(design, 'designInfo', 'interventionModel'),
                masking=self._safe_get(design, 'designInfo', 'maskingInfo', 'masking'),
                primary_purpose=self._safe_get(design, 'designInfo', 'primaryPurpose'),
                
                # Participants
                enrollment_count=self._safe_get(design, 'enrollmentInfo', 'count'),
                enrollment_type=self._safe_get(design, 'enrollmentInfo', 'type'),
                eligibility_criteria=eligibility.get('eligibilityCriteria', ''),
                healthy_volunteers=eligibility.get('healthyVolunteers', ''),
                gender=eligibility.get('sex', ''),
                minimum_age=eligibility.get('minimumAge', ''),
                maximum_age=eligibility.get('maximumAge', ''),
                
                # Conditions and Interventions
                conditions=conditions.get('conditions', []),
                interventions=[
                    {
                        'type': intervention.get('type', ''),
                        'name': intervention.get('name', ''),
                        'description': intervention.get('description', ''),
                        'arm_group_labels': intervention.get('armGroupLabels', [])
                    }
                    for intervention in arms_interventions.get('interventions', [])
                ],
                keywords=conditions.get('keywords', []),
                
                # Outcomes
                primary_outcomes=[
                    {
                        'measure': outcome.get('measure', ''),
                        'description': outcome.get('description', ''),
                        'time_frame': outcome.get('timeFrame', '')
                    }
                    for outcome in outcomes.get('primaryOutcomes', [])
                ],
                secondary_outcomes=[
                    {
                        'measure': outcome.get('measure', ''),
                        'description': outcome.get('description', ''),
                        'time_frame': outcome.get('timeFrame', '')
                    }
                    for outcome in outcomes.get('secondaryOutcomes', [])
                ],
                other_outcomes=[
                    {
                        'measure': outcome.get('measure', ''),
                        'description': outcome.get('description', ''),
                        'time_frame': outcome.get('timeFrame', '')
                    }
                    for outcome in outcomes.get('otherOutcomes', [])
                ],
                
                # Sponsors and Collaborators
                lead_sponsor={
                    'name': self._safe_get(sponsor_collaborators, 'leadSponsor', 'name', default=''),
                    'class': self._safe_get(sponsor_collaborators, 'leadSponsor', 'class', default='')
                },
                collaborators=[
                    {
                        'name': collab.get('name', ''),
                        'class': collab.get('class', '')
                    }
                    for collab in sponsor_collaborators.get('collaborators', [])
                ],
                
                # Locations
                locations=[
                    {
                        'facility': location.get('facility', ''),
                        'city': location.get('city', ''),
                        'state': location.get('state', ''),
                        'country': location.get('country', ''),
                        'zip': location.get('zip', ''),
                        'status': location.get('status', '')
                    }
                    for location in contacts_locations.get('locations', [])
                ],
                
                # Contact Information
                overall_officials=[
                    {
                        'name': official.get('name', ''),
                        'affiliation': official.get('affiliation', ''),
                        'role': official.get('role', '')
                    }
                    for official in contacts_locations.get('overallOfficials', [])
                ],
                central_contacts=[
                    {
                        'name': contact.get('name', ''),
                        'role': contact.get('role', ''),
                        'phone': contact.get('phone', ''),
                        'email': contact.get('email', '')
                    }
                    for contact in contacts_locations.get('centralContacts', [])
                ],
                
                # Publications and References
                references=[
                    {
                        'pmid': ref.get('pmid', ''),
                        'type': ref.get('type', ''),
                        'citation': ref.get('citation', '')
                    }
                    for ref in references.get('references', [])
                ],
                results_references=[
                    {
                        'pmid': ref.get('pmid', ''),
                        'type': ref.get('type', ''),
                        'citation': ref.get('citation', '')
                    }
                    for ref in references.get('seeAlsoLinks', [])
                ],
                
                # Results Data
                has_results=bool(results),
                results_first_posted_date=self._extract_date(results.get('resultsFirstPostDateStruct')) if results else None,
                participant_flow=results.get('participantFlowModule') if results else None,
                baseline_characteristics=results.get('baselineCharacteristicsModule') if results else None,
                outcome_measures=results.get('outcomeMeasuresModule') if results else None,
                adverse_events=results.get('adverseEventsModule') if results else None,
                
                # Additional Information
                brief_summary=description.get('briefSummary', ''),
                detailed_description=description.get('detailedDescription', ''),
                study_docs=[
                    {
                        'type': doc.get('type', ''),
                        'url': doc.get('url', ''),
                        'comment': doc.get('comment', '')
                    }
                    for doc in ipdsharing.get('studyDocs', [])
                ]
            )
            
            return True, comprehensive_info
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive data for NCT {nct_id}: {str(e)}")
            return False, None
    
    def save_to_json(self, data: Any, filename: str, output_dir: str = "output") -> str:
        """
        Save data to a JSON file for testing purposes.
        
        Args:
            data: Data to save (can be dict, list, or dataclass)
            filename: Name of the JSON file
            output_dir: Directory to save the file in
            
        Returns:
            Full path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert dataclass to dict if needed
        if hasattr(data, '__dataclass_fields__'):
            data = asdict(data)
        elif isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            data = [asdict(item) for item in data]
        
        # Add timestamp to filename if it doesn't have extension
        if not filename.endswith('.json'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}.json"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Data saved to: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save data to {filepath}: {str(e)}")
            raise
    
    def test_comprehensive_nct_data(self, nct_numbers: List[str]) -> Dict[str, Any]:
        """
        Test comprehensive NCT data retrieval and save results to JSON.
        
        Args:
            nct_numbers: List of NCT numbers to test
            
        Returns:
            Dictionary with test results
        """
        self.logger.info(f"Testing comprehensive data retrieval for {len(nct_numbers)} numbers")
        
        results = {
            'test_timestamp': datetime.now().isoformat(),
            'total_tested': len(nct_numbers),
            'valid_count': 0,
            'invalid_count': 0,
            'studies': [],
            'errors': []
        }
        
        for nct_id in nct_numbers:
            try:
                is_valid, study_info = self.get_comprehensive_study_data(nct_id)
                
                if is_valid and study_info:
                    results['valid_count'] += 1
                    results['studies'].append(asdict(study_info))
                    self.logger.info(f"✓ Retrieved comprehensive data: {nct_id}")
                else:
                    results['invalid_count'] += 1
                    results['errors'].append({
                        'nct_id': nct_id,
                        'error': 'Invalid or not found'
                    })
                    self.logger.warning(f"✗ Invalid: {nct_id}")
                    
            except Exception as e:
                results['invalid_count'] += 1
                results['errors'].append({
                    'nct_id': nct_id,
                    'error': str(e)
                })
                self.logger.error(f"✗ Error testing {nct_id}: {str(e)}")
        
        # Save results to JSON
        filename = f"comprehensive_nct_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_to_json(results, filename)
        
        self.logger.info(f"Comprehensive data test complete: {results['valid_count']} valid, {results['invalid_count']} invalid")
        return results
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        valid_entries = sum(1 for key in self.cache if self._is_cache_valid(key))
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("API cache cleared") 