# Clinical Trial Data Extraction System

A production-ready system for extracting structured data from clinical trial PDFs using OpenAI GPT models. This system processes medical research papers to extract key clinical trial information for pharmaceutical and medical research analysis.

## 🎯 Features

- **Multi-stage Extraction**: Critical fields → Yes/No fields → Efficacy data → Safety data
- **Quality Control**: Built-in validation and QC extraction for accuracy assessment
- **Batch Processing**: Handle multiple PDFs efficiently with configurable batch sizes
- **Cost Tracking**: Monitor token usage and API costs
- **Flexible Processing**: Support both abstract-only and full publication modes
- **Structured Output**: Generate standardized CSV and Excel outputs with QC validation

## 🏗️ Architecture

```
PDF → Text Extraction → Multi-Stage LLM Processing → QC Validation → Excel/CSV Output
```

### Core Modules

- `src/openai_client.py`: GPT API calls, token counting, cost tracking, multi-stage extraction
- `src/prompts.py`: All LLM prompts and field-type-specific prompt generation
- `src/pdf_processor.py`: PDF text extraction and section parsing
- `src/excel_generator.py`: Output file generation with QC color coding
- `src/qc_*.py`: Quality control extraction and validation
- `main.py`: Orchestration and batch processing

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/schivam18/doctorci.git
cd doctorci
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Usage

#### Test Single PDF
```bash
python test_multi_stage.py resources/15.pdf
```

#### Run Full Extraction
```bash
# Abstract-only mode
python main.py

# Full publication mode
export PROCESS_MODE="full_pub"
python main.py
```

#### Clear Previous Data
```bash
python clear_data.py
```

## 📊 Output Structure

The system generates structured outputs in the `output/` directory:

- `combined.csv`: Main extraction results with all keywords
- `qc_results.csv`: Quality control validation results
- `compared_data.csv`: Comparison between extraction and QC
- `batch_summary.json`: Processing statistics and performance metrics

### Field Categories

- **Critical Fields**: NCT number, drug names, cancer type, trial phase
- **Yes/No Fields**: Binary outcomes and trial characteristics
- **Efficacy Data**: Response rates, progression-free survival, overall survival
- **Safety Data**: Adverse events, toxicity profiles

## 🔧 Configuration

### Keywords Structure
Field definitions are stored in:
- `data/keywords_structure_full_pub.json`: Full publication fields
- `data/keywords_structure.json`: Abstract-only fields

### Processing Modes
- `abstract`: Extract from abstract only (faster, lower cost)
- `full_pub`: Extract from full publication (comprehensive, higher cost)

## 🏥 Domain-Specific Rules

### Clinical Trial Terminology
- **NCT Number**: Format as "NCT########" (8 digits)
- **Drug Combinations**: Use "Drug A + Drug B" format
- **Cancer Staging**: Only Stage I, I/II, II, II/III, III, III/IV, IV
- **Response Rates**: Extract numbers only (remove % signs)
- **P-values and Hazard Ratios**: Preserve decimal precision

### Field Format Requirements
- **YES/NO fields**: Only "YES" or "NO" - no other values
- **Percentage fields**: Extract number only (45% → "45")
- **Numeric fields**: Numbers only, no units or text
- **Missing data**: Use "Not mentioned" consistently

## 📈 Performance Monitoring

The system tracks:
- Token usage per extraction stage
- API costs and rate limiting
- Processing time per PDF
- Success/failure rates
- QC validation accuracy

## 🛠️ Development

### Adding New Features
1. Update `keywords_structure_full_pub.json` for new fields
2. Add field-type-specific prompts in `src/prompts.py`
3. Update multi-stage extraction in `src/openai_client.py`
4. Add corresponding QC fields if critical
5. Update tests and documentation

### Debugging Extraction Issues
- Check `logs/clinical_trial_extraction_*.log` for detailed traces
- Examine `output/compared_data.csv` for QC validation results
- Use `test_multi_stage.py` for isolated testing
- Verify prompt formatting and JSON parsing

## 📝 Logging

Comprehensive logging is implemented using `src/logger_config.py`:
- Processing progress and errors
- Token usage and cost tracking
- QC validation results
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review the documentation in `docs/`
- Open an issue on GitHub

## 🔗 Related Projects

Based on the architecture and patterns from:
- [drug-detective](https://github.com/schivam18/drug-detective): Modular pipeline for extracting structured drug information
- [oncology-aggregator](https://github.com/schivam18/oncology-aggregator): Specialized platform for oncology research content 