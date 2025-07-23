# Development Guide

## 🚀 **Quick Start for Developers**

### **Initial Setup**
```bash
# Clone repository and setup environment
git clone <repository-url>
cd doctorci

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your OpenAI API key
```

### **Development Workflow**
```bash
# 1. Clear previous data (recommended for fresh runs)
python clear_data.py

# 2. Process PDFs with Marker
python marker_enhanced_pipeline.py

# 3. Run enhanced batch processing
python batch_enhanced_system.py

# 4. Examine results in sequential batch directory
ls output/batch_output_1/
```

---

## 🔧 **Adding New Fields**

### **Step 1: Update Keywords Structure**
Edit `data/keywords_structure_full_pub.json`:
```json
{
  "General": [...],
  "Efficacy": [...],
  "Safety": [
    ...,
    "New Safety Field"
  ]
}
```

### **Step 2: Add to Field-Specific Prompts**
Edit `src/prompts.py` - Add to appropriate prompt:
```python
def generate_field_type_specific_prompt(section_text: str, field_group: str) -> str:
    # ... existing code ...
    elif field_group == "safety":
        return f"""
        ...
        {{
            ...
            "New Safety Field": "number_only"
        }}
        ...
        """
```

### **Step 3: Update QC Fields (if critical)**
Edit `src/qc_extractor.py` if the field requires QC validation:
```python
QC_KEYWORDS = [
    # ... existing fields ...
    "New Safety Field"  # Add if critical for validation
]
```

### **Step 4: Test the New Field**
```bash
# Test extraction with the new field
python test_multi_stage.py resources/test.pdf

# Check if field appears in output JSON
cat test_extraction_test.json | grep "New Safety Field"
```

---

## 🐛 **Debugging Guide**

### **Common Issues & Solutions**

#### **1. Extraction Returns Empty Values**
```bash
# Check logs for API errors
tail -f logs/clinical_trial_extraction_*.log

# Verify prompt format
python -c "
from src.prompts import generate_field_type_specific_prompt
print(generate_field_type_specific_prompt('test text', 'critical'))
"

# Test with smaller text sample
python test_multi_stage.py resources/small.pdf
```

#### **2. JSON Parsing Errors**
```bash
# Check raw API responses
# Add debug logging in openai_client.py:
import json
print(f"Raw response: {response}")
try:
    parsed = json.loads(response)
except json.JSONDecodeError as e:
    print(f"JSON error at position {e.pos}: {e.msg}")
```

#### **3. Token Limit Exceeded**
```bash
# Check token counts per stage
python -c "
from src.openai_client import OpenAIClient
client = OpenAIClient()
text = 'your long text here'
print(f'Token count: {client.count_tokens(text)}')
"

# Solution: Split large sections or reduce field count per stage
```

#### **4. QC Validation Always Red**
```bash
# Check QC field extraction
python -c "
from src.qc_extractor import QCOpenAIClient
qc_client = QCOpenAIClient()
result = qc_client.extract_qc_fields('your text')
print(result)
"

# Verify validation logic
python -c "
from src.qc_validator import QCValidator
validator = QCValidator()
# Test with sample data
"
```

#### **5. Batch Processing Issues**
```bash
# Check input directory structure
ls -la input/marker_preprocessed/

# Verify file naming convention
# Should be: 6.json, 6.md, 7.json, 7.md, etc.

# Check batch output directory
ls -la output/batch_output_1/
```

### **Debugging Tools**

#### **Enable Debug Logging**
```python
# In main.py or test scripts:
import logging
setup_logging(logging.DEBUG)  # Instead of INFO
```

#### **Inspect API Calls**
```python
# Add to openai_client.py temporarily:
def get_completion(self, messages, max_tokens=4000):
    print(f"PROMPT: {messages}")
    response = self.client.chat.completions.create(...)
    print(f"RESPONSE: {response.choices[0].message.content}")
    return response.choices[0].message.content
```

#### **Manual Testing Commands**
```bash
# Test PDF text extraction only
python -c "
from src.full_pub_processor import extract_text_from_full_pdf
sections = extract_text_from_full_pdf('resources/15.pdf')
for name, content in sections.items():
    print(f'{name}: {len(content)} chars')
"

# Test single stage extraction
python -c "
from src.openai_client import OpenAIClient
from src.prompts import generate_field_type_specific_prompt
client = OpenAIClient()
prompt = generate_field_type_specific_prompt('test text', 'critical')
response = client.get_completion([{'role': 'user', 'content': prompt}])
print(response)
"
```

---

## 📊 **Performance Optimization**

### **Monitoring API Costs**
```python
# Track costs during development
client = OpenAIClient()
# ... processing ...
client.print_usage_summary()

# Expected costs (GPT-4o-mini):
# - Single PDF: ~$0.006
# - 10 PDFs: ~$0.06
# - 100 PDFs: ~$0.60
```

### **Optimizing Token Usage**
```python
# Before optimization
total_tokens = len(full_text) + len(all_fields_prompt)  # Often >16K

# After multi-stage optimization
stage_tokens = len(section_text) + len(focused_prompt)  # Usually <5K per stage
```

### **Parallel Processing (Future Enhancement)**
```python
# Current: Sequential processing
for pdf in pdfs:
    process_pdf(pdf)

# Future: Parallel processing
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_pdf, pdf) for pdf in pdfs]
```

---

## 🧪 **Testing Strategy**

### **Unit Testing**
```bash
# Test individual components
python -m pytest tests/test_pdf_processor.py
python -m pytest tests/test_prompts.py
python -m pytest tests/test_qc_validator.py
```

### **Integration Testing**
```bash
# Test complete pipeline on known good PDF
python test_multi_stage.py resources/known_good.pdf

# Verify output format
python -c "
import pandas as pd
df = pd.read_csv('output/batch_output_1/validated_6.csv')
print(f'Columns: {list(df.columns)}')
print(f'Rows: {len(df)}')
print(f'Non-empty fields: {df.notna().sum().sum()}')
"
```

### **Regression Testing**
```bash
# Compare current vs previous extraction results
python scripts/compare_extractions.py output/batch_output_1/validated_6.csv output/batch_output_2/validated_6.csv

# Expected stability metrics:
# - NCT numbers: 100% match
# - Drug names: >95% match  
# - Response rates: >90% match (±5% tolerance)
```

---

## 📈 **Extending the System**

### **Adding New Processing Modes**
```python
# In main.py, add new mode:
if mode == 'abstract':
    # existing abstract processing
elif mode == 'full_pub':
    # existing full publication processing
elif mode == 'custom_mode':
    # new processing logic
```

### **Custom Field Validators**
```python
# Create custom validation in qc_validator.py:
def validate_custom_field(original_value, qc_value, field_name):
    if field_name == "Special Field":
        # Custom validation logic
        return custom_match_score
    else:
        return default_validation(original_value, qc_value)
```

### **Output Format Extensions**
```python
# Add new output formats in excel_generator.py:
def generate_custom_report(data, output_dir):
    # Generate custom report format
    # Could be JSON, XML, database insert, etc.
```

---

## 🔒 **Security & Best Practices**

### **API Key Management**
```bash
# Never commit API keys
echo "OPENAI_API_KEY=sk-..." >> .env
echo ".env" >> .gitignore

# Use environment variables in production
export OPENAI_API_KEY="sk-..."
```

### **Data Privacy**
```python
# Ensure no sensitive data in logs
logger.info(f"Processing PDF: {os.path.basename(pdf_path)}")  # Good
logger.info(f"API response: {response}")  # Bad - may contain data
```

### **Error Handling**
```python
# Always handle exceptions gracefully
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Expected error: {e}")
    return fallback_value
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise  # Re-raise unexpected errors
```

---

## 📚 **Code Review Checklist**

### **Before Submitting Code**
- [ ] All new functions have type hints
- [ ] Comprehensive error handling added
- [ ] Logging statements include context
- [ ] No hardcoded file paths or constants
- [ ] API usage is cost-optimized
- [ ] Documentation updated for new features
- [ ] Test script validates changes
- [ ] Output format remains consistent
- [ ] File naming follows simplified convention
- [ ] Batch processing uses sequential directories

### **Review Focus Areas**
- [ ] Token usage optimization
- [ ] Error handling coverage
- [ ] Logging clarity and completeness
- [ ] Field format compliance
- [ ] QC validation accuracy
- [ ] Performance impact assessment
- [ ] API cost tracking implementation
- [ ] File organization and naming

---

## 📁 **File Organization Standards**

### **Input Directory Structure**
```
input/
└── marker_preprocessed/
    ├── 6.json              # Simplified naming: pdf_number.json
    ├── 6.md                # Simplified naming: pdf_number.md
    ├── 7.json
    ├── 7.md
    └── summary.json        # Processing summary (no timestamp)
```

### **Output Directory Structure**
```
output/
├── batch_output_1/         # Sequential batch directories
│   ├── validated_6.csv     # Individual results
│   ├── validated_6.json    # Structured data
│   ├── raw_llm_6.json      # Raw API responses
│   ├── combined.csv        # All results combined
│   └── batch_summary.json  # Processing summary + API costs
├── batch_output_2/         # Next batch run
└── batch_output_n/         # Future batch runs
```

### **File Naming Convention**
- **Input files**: `pdf_number.json`, `pdf_number.md`
- **Output files**: `validated_pdf_number.csv`, `raw_llm_pdf_number.json`
- **Batch files**: `combined.csv`, `batch_summary.json`
- **No timestamps**: Clean, consistent naming for easy processing

---

## 💰 **API Cost Management**

### **Cost Tracking Implementation**
```python
# Real-time cost monitoring in OpenAIClient
def _update_totals(self, prompt_tokens: int, completion_tokens: int, cost: float):
    self.total_prompt_tokens += prompt_tokens
    self.total_completion_tokens += completion_tokens
    self.total_cost += cost
    self.request_count += 1

# Usage summary in batch processing
api_usage = client.get_usage_summary()
print(f"💰 Total cost: ${api_usage['total_cost']:.6f}")
```

### **Cost Optimization Strategies**
- **Multi-stage processing**: Reduces token usage by 40%
- **Focused prompts**: Better accuracy with fewer tokens
- **Efficient retry logic**: Minimizes failed API calls
- **Real-time monitoring**: Track costs during development

### **Expected Costs**
- **Single PDF**: ~$0.006
- **10 PDFs**: ~$0.06
- **100 PDFs**: ~$0.60
- **1000 PDFs**: ~$6.00

---

## 🔄 **Batch Processing Workflow**

### **1. Batch Initialization**
```python
# Create sequential batch directory
batch_counter = 1
while os.path.exists(f"output/batch_output_{batch_counter}"):
    batch_counter += 1
output_dir = f"output/batch_output_{batch_counter}"
```

### **2. File Processing**
```python
# Process each preprocessed markdown file
for markdown_file in input/marker_preprocessed/*.md:
    result = process_single_markdown(markdown_file)
    # Generate individual outputs with simplified naming
```

### **3. Combined Output Generation**
```python
# Create combined CSV with flattened treatment arms
combined_csv = create_combined_csv(results, output_dir)
# Save as combined.csv (no timestamp)
```

### **4. Summary and Cost Tracking**
```python
# Include API usage in batch summary
api_usage = client.get_usage_summary()
batch_summary = {
    "batch_metadata": {...},
    "api_usage": api_usage,
    "results": results
}
``` 