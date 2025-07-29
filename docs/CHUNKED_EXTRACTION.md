# Chunked Clinical Trial Data Extraction

## Overview

The chunked extraction approach replaces the single mega-prompt with a deterministic, arm-aware, chunked-prompt system that significantly improves accuracy and reduces hallucination risk.

## Architecture

### 10-Chunk System

The system divides extraction into 10 focused chunks:

1. **Chunk 0**: Arm Discovery
   - Identifies all treatment arms
   - Returns arm metadata (ID, generic name, dose, patient count)

2. **Chunk 1**: Publication & Trial Metadata
   - Journal, year, PDF#, NCT, phase, sponsors

3. **Chunk 2**: Population & Baseline
   - Cancer type, prior therapy flags, mutation status, median age

4. **Chunk 3**: Treatment Descriptors
   - Generic/brand names, MoA, target, dosing, company info

5. **Chunk 4**: Survival Endpoints
   - PFS, OS, EFS, RFS, MFS medians, HR, p-values

6. **Chunk 5**: Time-to Metrics
   - TTR, TTP, TTNT, TTF, DOR

7. **Chunk 6**: Response Rates
   - ORR, CR, pCR, CMR, DCR, CBR, rate grids

8. **Chunk 7**: Safety Header
   - AE class detection, overall %, grade ≥3%, serious, discontinuation

9. **Chunk 8**: Safety Grade ≥3 Sub-events
   - Immune, CRS, heme, GI, pulmonary, endocrine, hepatic, skin

10. **Chunk 9**: Geography & Timeline
    - Study dates, first results, EU/US/CN locations

## Key Benefits

### 1. Reduced Hallucination Risk
- **Temperature 0**: Deterministic extraction
- **Focused prompts**: Each chunk targets specific data types
- **Explicit instructions**: "Never infer, leave blank if not found"
- **Token limits**: Prevents rambling responses

### 2. Improved Table Handling
- **CSV conversion**: Markdown tables converted to CSV format
- **Structured extraction**: Better handling of tabular data
- **Arm context**: Each chunk includes arm identification

### 3. Cost Optimization
- **Smaller prompts**: ~70% reduction in prompt size
- **Focused calls**: Each chunk < 4k tokens
- **Efficient processing**: ~17 calls per paper (2 arms)

### 4. Arm-Aware Processing
- **Discovery first**: Identifies all arms before extraction
- **Arm-specific chunks**: Chunks 2-8 processed per arm
- **Shared data**: Chunks 1 & 9 processed once per paper

## Implementation

### Core Components

#### 1. Chunk Templates (`src/chunk_templates.py`)
```python
CHUNK_FIELD_MAP = {
    0: [],  # Arm discovery
    1: ["Publication Name", "Publication Year", ...],
    # ... field mappings for each chunk
}

def get_arm_discovery_prompt(publication_text: str) -> str:
    # Generates arm discovery prompt

def get_chunk_prompt(publication_text: str, arm: dict, chunk_id: int) -> str:
    # Generates arm-specific chunk prompt

def get_shared_chunk_prompt(publication_text: str, chunk_id: int) -> str:
    # Generates shared (publication-level) chunk prompt
```

#### 2. Enhanced Extractor (`src/enhanced_extractor.py`)
```python
class EnhancedClinicalExtractor:
    def detect_arms(self, publication_text: str) -> Dict[str, Any]:
        # Stage 1: Arm discovery
    
    def build_chunk_prompt(self, publication_text: str, arm: Optional[Dict], chunk_id: int) -> Dict[str, Any]:
        # Builds prompts for specific chunks
    
    def merge_chunk_results(self, arm_id: str, shared_data: Dict, arm_partials: List[Dict]) -> Dict:
        # Merges chunk results into final arm-level JSON
    
    def extract_tables_as_csv(self, publication_text: str) -> str:
        # Converts markdown tables to CSV for LLM processing
```

#### 3. OpenAI Client (`src/openai_client.py`)
```python
class OpenAIClient:
    def extract_full_publication_chunked(self, full_text: str) -> Optional[Dict[str, Any]]:
        # Complete chunked extraction pipeline
        # 1. Discover arms
        # 2. Extract shared data (chunks 1 & 9)
        # 3. Extract arm-specific data (chunks 2-8 per arm)
        # 4. Merge results
```

### Processing Flow

```
Publication Text
       ↓
   Arm Discovery (Chunk 0)
       ↓
   Shared Extraction (Chunks 1 & 9)
       ↓
   For each arm:
       ↓
   Arm-Specific Extraction (Chunks 2-8)
       ↓
   Merge Results
       ↓
   Final Publication JSON
```

## Usage

### Testing Single File
```bash
# Test chunked extraction on a single markdown file
python test_chunked_extraction.py
```

### Batch Processing
```bash
# Process all markdown files with chunked approach
python batch_enhanced_system.py
```

### Programmatic Usage
```python
from src.openai_client import OpenAIClient

client = OpenAIClient()
result = client.extract_full_publication_chunked(publication_text)
```

## Performance Metrics

### Cost Analysis
- **Per paper (2 arms)**: ~17 LLM calls
- **Per call**: ~250 completion tokens
- **Total cost**: ~$0.0025 per paper
- **vs. mega-prompt**: ~70% cost reduction

### Accuracy Improvements
- **Table extraction**: Better handling of structured data
- **Arm separation**: Clear distinction between treatment arms
- **Missing data**: Explicit handling of absent information
- **Validation**: Per-chunk and final validation

### Processing Time
- **Per paper**: ~15-20 seconds
- **Parallel processing**: Can process multiple arms simultaneously
- **Error resilience**: Individual chunk failures don't break pipeline

## Validation & Quality Control

### Per-Chunk Validation
- **JSON parsing**: Robust error handling
- **Field validation**: Type and range checking
- **Missing data**: Consistent handling of absent values

### Final Validation
- **Arm consistency**: Cross-arm validation
- **Data integrity**: Format and range checks
- **Completeness**: Required field validation

### Error Handling
- **Graceful degradation**: Failed chunks don't break pipeline
- **Retry logic**: Automatic retry for failed calls
- **Comprehensive logging**: Detailed error tracking

## Migration from Mega-Prompt

### Backward Compatibility
- **Legacy methods**: Still available for transition
- **Gradual migration**: Can run both approaches
- **Data comparison**: Compare results between approaches

### Configuration
```python
# Use chunked approach
result = client.extract_full_publication_chunked(text)

# Use legacy approach (still available)
result = client.extract_publication_data(text)
```

## Future Enhancements

### Planned Improvements
1. **Function calling**: Direct JSON schema validation
2. **Caching**: Cache arm discovery results
3. **Reconciliation**: Cross-publication validation
4. **Gradio UI**: Interactive testing interface
5. **Parallel processing**: Async arm processing

### Advanced Features
- **Smart chunking**: Dynamic chunk size based on content
- **Context optimization**: Intelligent text truncation
- **Multi-model**: Use different models for different chunks
- **Quality scoring**: Confidence metrics per chunk

## Troubleshooting

### Common Issues

#### 1. Arm Discovery Failures
```python
# Check NCT number presence
if not re.search(r"NCT\d{8}", text):
    print("No NCT number found")
```

#### 2. Chunk Processing Errors
```python
# Validate JSON responses
try:
    chunk_data = json.loads(response)
except json.JSONDecodeError:
    print("Invalid JSON response")
```

#### 3. Table Extraction Issues
```python
# Check table format
tables = re.findall(r'\|.*?\|\n(?:\|.*?\|\n)+', text)
if not tables:
    print("No markdown tables found")
```

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### 1. Prompt Design
- **Be specific**: Clear field definitions
- **Set boundaries**: Explicit "do not guess" instructions
- **Provide examples**: Show expected output format

### 2. Error Handling
- **Graceful degradation**: Continue processing on chunk failures
- **Retry logic**: Automatic retry for transient errors
- **Comprehensive logging**: Track all operations

### 3. Performance Optimization
- **Batch processing**: Process multiple files efficiently
- **Token management**: Monitor token usage
- **Cost tracking**: Track API costs per extraction

### 4. Quality Assurance
- **Validation**: Multi-level data validation
- **Testing**: Comprehensive test suite
- **Monitoring**: Track accuracy metrics

## Conclusion

The chunked extraction approach represents a significant improvement over the single mega-prompt system, providing:

- **Better accuracy**: Focused prompts reduce hallucination
- **Lower costs**: Smaller, targeted prompts
- **Improved reliability**: Arm-aware processing
- **Enhanced maintainability**: Modular, testable components

This architecture provides a solid foundation for clinical trial data extraction while maintaining the flexibility to adapt to new requirements and data formats.