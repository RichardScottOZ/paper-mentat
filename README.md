# paper-mentat

Search, verify open access status, and retrieve academic papers. Uses real scholarly APIs (Crossref, Unpaywall, OpenAlex, arXiv, PubMed) with optional LLM-enhanced metadata extraction.

## Install

```bash
pip install -e .
```

Or just:
```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Search for papers
paper-mentat --query "machine learning mineral exploration"

# Search multiple topics
paper-mentat --topics "geophysics" "remote sensing" "geochemistry"

# Process a list of DOIs/URLs
paper-mentat --paper-list mineral_exploration_papers.txt

# Download open access PDFs
paper-mentat --query "deep learning geology" --download-pdfs

# Use config file
paper-mentat --config config.yaml
```

Or run directly:
```bash
python -m paper_mentat.cli --query "machine learning mineral exploration"
```

## Configuration

Copy and edit `config.yaml`:

```yaml
# Your email - needed for Unpaywall API (the best OA checker)
contact_email: "you@example.com"

# Topics for batch search
topics_of_interest:
  - "machine learning mineral exploration"
  - "deep learning geology"

output_dir: "results"
```

Setting `contact_email` enables Unpaywall integration, which is the most reliable way to find open access PDFs.

## How It Works

1. **Search** across arXiv, Crossref, and OpenAlex simultaneously
2. **Verify OA status** via Unpaywall (primary) with OpenAlex fallback
3. **Download PDFs** from verified open access sources
4. **Save results** as JSON with full metadata

### Paper List Format

Text files with DOIs and/or URLs, one per line. Comments with `#`:

```
# Machine Learning in Mineral Exploration
10.1016/j.oregeorev.2018.12.018
10.1016/j.oregeorev.2019.103107

# arXiv papers
https://arxiv.org/abs/1901.01234
```

## API Usage

```python
from paper_mentat import AcademicPaperFramework

fw = AcademicPaperFramework("config.yaml")

# Search
results = fw.search_ad_hoc("machine learning mineral exploration", max_results=20)

# Process DOI list
results = fw.process_paper_list("papers.txt")

# Download PDFs
fw.download_pdfs(results)

# Save & report
fw.save_results(results, "output.json")
print(fw.generate_report(results))
```

## Optional: LLM Enhancement

Enable Ollama or OpenAI for richer metadata extraction:

```bash
paper-mentat --query "AI geology" --enable-llm --ollama-model llama2
```

## CLI Options

```
--query TEXT          Ad-hoc search query
--topics TEXT [TEXT]   Topic-based search
--paper-list FILE     File of DOIs/URLs
--config FILE         YAML config file
--max-results N       Max results (default: 50)
--output FILE         Output JSON filename
--download-pdfs       Download open access PDFs
--report-only         Print report, don't save JSON
--enable-llm          Enable LLM metadata enhancement
--llm-provider        ollama or openai
--ollama-model        Ollama model name
-v, --verbose         Debug logging
```

## License

MIT
