# Academic Paper Search Framework

A modular, AI-driven framework for autonomous identification and retrieval of open access scholarly literature, specifically designed for mineral exploration and machine learning research.

## Features

- **Ad-hoc Manual Search**: Search for papers using specific queries
- **Configurable Topic-based Search**: Set up topics of interest and search automatically
- **Paper List Processing**: Process lists of papers from files (DOIs, URLs)
- **Multi-stage Processing Pipeline**: State-driven architecture for robust processing
- **Open Access Detection**: Identify and retrieve open access papers
- **PDF Download**: Automatically download PDFs of open access papers
- **Comprehensive Reporting**: Generate detailed reports of search results

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd academic-paper-framework
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install enhanced functionality:
```bash
pip install unpywall habanero playwright openai
```

## Quick Start

### 1. Ad-hoc Search
Search for papers on a specific topic:
```bash
python academic_paper_cli.py --query "machine learning mineral exploration"
```

### 2. Topic-based Search
Search multiple topics:
```bash
python academic_paper_cli.py --topics "geophysics" "remote sensing" "geochemistry"
```

### 3. Process Paper List
Process papers from a file:
```bash
python academic_paper_cli.py --paper-list mineral_exploration_papers.txt
```

### 4. Use Configuration File
Use a configuration file for automated searches:
```bash
python academic_paper_cli.py --config config.yaml
```

## Configuration

The framework uses YAML configuration files. Example `config.yaml`:

```yaml
# Basic settings
rate_limit_per_second: 1
max_retries: 3
timeout: 30
user_agent: 'AcademicPaperFramework/1.0 (research-agent)'

# Output settings
output_dir: 'results'
save_pdfs: true

# Topics of interest
topics_of_interest:
  - "machine learning mineral exploration"
  - "geophysics remote sensing"
  - "geochemistry data analysis"
  - "deep learning geology"

# Paper lists to process
paper_lists:
  - "mineral_exploration_papers.txt"
  - "machine_learning_geology_papers.txt"
```

## Paper List Format

Create text files with DOIs and URLs. Example `papers.txt`:

```
# Machine Learning in Mineral Exploration
10.1016/j.oregeorev.2018.12.018
10.1016/j.oregeorev.2019.103107

# Additional URLs
https://arxiv.org/abs/1901.01234
https://www.researchgate.net/publication/123456789_Machine_Learning_in_Mineral_Exploration
```

## Architecture

The framework implements a modular, state-driven architecture based on the design described in `academic-papers-reports.md`:

### Module 1: URL Ingestion and Content Triage
- Validates URLs and checks for scholarly content
- Filters out non-scholarly resources
- Performs lightweight HTTP HEAD requests

### Module 2: Scholarly Content Identification and Metadata Extraction
- Extracts paper titles, authors, DOIs, abstracts
- Uses heuristic-based classification
- Supports LLM-enhanced extraction (optional)

### Module 3: Open Access Status Verification
- Checks OA status using multiple APIs
- Supports Unpaywall, Crossref, OpenAlex
- Determines best available PDF location

### Module 4: Conditional and Compliant PDF Retrieval
- Downloads PDFs from verified OA sources
- Implements ethical scraping practices
- Handles complex publisher websites

## Usage Examples

### Search for Mineral Exploration Papers
```bash
# Search for machine learning in mineral exploration
python academic_paper_cli.py --query "machine learning mineral exploration" --max-results 100

# Search multiple related topics
python academic_paper_cli.py --topics "geophysics" "remote sensing" "geochemistry" --max-results 50
```

### Process Your Paper List
```bash
# Process papers from your mineral exploration readme
python academic_paper_cli.py --paper-list your_papers.txt --output results.json
```

### Use Configuration for Automated Searches
```bash
# Use the provided config with mineral exploration topics
python academic_paper_cli.py --config config.yaml
```

### Advanced Options
```bash
# Skip PDF download (metadata only)
python academic_paper_cli.py --query "deep learning geology" --no-pdfs

# Generate report only
python academic_paper_cli.py --query "AI mining" --report-only

# Verbose output
python academic_paper_cli.py --query "computer vision geology" --verbose
```

## Output

The framework generates:

1. **JSON Results File**: Complete metadata and processing results
2. **PDF Downloads**: Open access papers saved to `results/` directory
3. **Summary Report**: Processing statistics and paper breakdown
4. **Sample Results**: Preview of found papers

Example output:
```
Academic Paper Search Report
===========================

Total URLs Processed: 50
Successfully Completed: 45
Failed: 5
Success Rate: 90.0%

Open Access Breakdown:
- Gold OA: 15
- Green OA: 30
- Total OA Papers: 45

Processing Time:
- Average: 2.34s
- Total: 117.00s

Top Journals:
- Ore Geology Reviews: 12
- Computers & Geosciences: 8
- Journal of Applied Geophysics: 6
```

## Integration with Your Mineral Exploration README

To integrate with your existing mineral exploration machine learning readme:

1. **Extract Paper References**: The framework can process any text file containing DOIs or URLs
2. **Add to Paper Lists**: Add your paper references to `mineral_exploration_papers.txt`
3. **Configure Topics**: Add your research topics to `config.yaml`
4. **Automated Processing**: Run the framework to retrieve and organize your papers

Example integration:
```bash
# Process your readme file
python academic_paper_cli.py --paper-list your_mineral_exploration_readme.md

# Search for papers mentioned in your readme
python academic_paper_cli.py --query "papers from your readme topic"
```

## Ethical and Legal Compliance

The framework implements responsible web scraping practices:

- **Respects robots.txt**: Checks and follows site policies
- **Rate Limiting**: Implements polite request pacing
- **Transparent Identification**: Uses proper User-Agent strings
- **Legal Compliance**: Only accesses publicly available content
- **No Authentication Bypass**: Never attempts to bypass paywalls

## Advanced Features

### LLM Integration (Optional)
Enable enhanced metadata extraction with OpenAI:
```yaml
openai_api_key: "your-api-key"
openai_model: "gpt-4"
enable_llm_enhancement: true
```

### Browser Automation (Optional)
Enable for complex publisher websites:
```yaml
enable_browser_automation: true
```

### Enhanced API Integration (Optional)
Enable full OA status checking:
```yaml
unpaywall_email: "your-email@example.com"
crossref_email: "your-email@example.com"
```

## Troubleshooting

### Common Issues

1. **No Results Found**: Check your query or paper list format
2. **Rate Limiting**: Reduce `rate_limit_per_second` in config
3. **PDF Download Failures**: Some publishers block automated downloads
4. **API Errors**: Check your API keys and email configurations

### Debug Mode
```bash
python academic_paper_cli.py --query "your query" --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This framework is based on the architectural design described in `academic-papers-reports.md` and implements best practices for scholarly literature retrieval. 