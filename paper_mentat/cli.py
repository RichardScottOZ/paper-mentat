"""Command-line interface for paper-mentat."""

import argparse
import logging
import sys
from pathlib import Path

from paper_mentat import AcademicPaperFramework


def main():
    parser = argparse.ArgumentParser(
        description="paper-mentat: Search, verify OA status, and retrieve academic papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --query "machine learning mineral exploration"
  %(prog)s --topics "geophysics" "remote sensing"
  %(prog)s --paper-list mineral_exploration_papers.txt
  %(prog)s --config config.yaml
  %(prog)s --query "deep learning geology" --download-pdfs
""",
    )
    # Input modes
    parser.add_argument("--query", help="Ad-hoc search query")
    parser.add_argument("--topics", nargs="+", help="Topic-based search")
    parser.add_argument("--paper-list", help="File of DOIs/URLs to process")
    parser.add_argument("--config", help="YAML config file")

    # Options
    parser.add_argument("--max-results", type=int, default=50, help="Max results (default: 50)")
    parser.add_argument("--output", help="Output JSON filename")
    parser.add_argument("--download-pdfs", action="store_true", help="Download OA PDFs")
    parser.add_argument("--new-only", action="store_true", help="Only show papers not seen in previous runs")
    parser.add_argument("--report-only", action="store_true", help="Print report only, don't save JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # LLM options
    parser.add_argument("--enable-llm", action="store_true", help="Enable LLM metadata enhancement")
    parser.add_argument("--llm-provider", choices=["ollama", "openai"], help="LLM provider")
    parser.add_argument("--ollama-model", help="Ollama model name")
    parser.add_argument("--ollama-base-url", help="Ollama API URL")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Build config overrides from CLI args
    config_path = args.config
    framework = AcademicPaperFramework(config_path)

    if args.enable_llm:
        framework.config["enable_llm_enhancement"] = True
    if args.llm_provider:
        framework.config["llm_provider"] = args.llm_provider
    if args.ollama_model:
        framework.config["ollama_model"] = args.ollama_model
    if args.ollama_base_url:
        framework.config["ollama_base_url"] = args.ollama_base_url
    if args.enable_llm:
        framework._setup_llm()

    # Run search
    results = []
    if args.query:
        print(f"🔍 Searching: {args.query}")
        results = framework.search_ad_hoc(args.query, args.max_results)
    elif args.topics:
        print(f"🔍 Searching topics: {args.topics}")
        per_topic = args.max_results // len(args.topics)
        results = framework.search_by_topics(args.topics, per_topic)
    elif args.paper_list:
        path = Path(args.paper_list)
        if not path.exists():
            print(f"❌ File not found: {args.paper_list}")
            sys.exit(1)
        print(f"📄 Processing: {args.paper_list}")
        results = framework.process_paper_list(args.paper_list)
    elif framework.config.get("topics_of_interest"):
        topics = framework.config["topics_of_interest"]
        print(f"🔍 Searching configured topics ({len(topics)} topics)")
        results = framework.search_by_topics(topics, args.max_results)
    else:
        print("❌ Specify --query, --topics, --paper-list, or use --config with topics_of_interest")
        sys.exit(1)

    if not results:
        print("❌ No results found.")
        sys.exit(1)

    # Filter to new only
    if args.new_only:
        all_count = len(results)
        results = framework.filter_new(results)
        print(f"📌 {len(results)} new papers (filtered from {all_count})")
        if not results:
            print("No new papers since last run.")
            sys.exit(0)

    # Report
    print(f"\n✅ Found {len(results)} papers\n")
    print(framework.generate_report(results))

    # Download PDFs
    if args.download_pdfs:
        count = framework.download_pdfs(results)
        print(f"\n📥 Downloaded {count} PDFs to {framework.config['output_dir']}/")

    # Save results
    if not args.report_only:
        out = framework.save_results(results, args.output)
        print(f"\n💾 Results saved to: {out}")

    # Mark as seen for future --new-only runs
    framework.mark_results_seen(results, downloaded_only=args.download_pdfs)

    # Sample output
    print("\n📋 Sample Results:")
    shown = 0
    for r in results:
        if shown >= 5:
            break
        if r.metadata and r.metadata.title:
            shown += 1
            m = r.metadata
            oa_tag = f" [{m.oa_status.value}]" if m.oa_status else ""
            print(f"  {shown}. {m.title}{oa_tag}")
            if m.authors:
                print(f"     Authors: {', '.join(m.authors[:3])}")
            if m.doi:
                print(f"     DOI: {m.doi}")
            if m.oa_url:
                print(f"     PDF: {m.oa_url}")
            print()


if __name__ == "__main__":
    main()
