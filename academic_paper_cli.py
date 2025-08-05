#!/usr/bin/env python3
"""
Command-line interface for the Academic Paper Search Framework
"""

import argparse
import sys
from pathlib import Path
from academic_paper_framework import AcademicPaperFramework

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Academic Paper Search Framework - A modular, AI-driven framework for scholarly literature retrieval',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ad-hoc search for a specific topic
  python academic_paper_cli.py --query "machine learning mineral exploration"
  
  # Search multiple topics
  python academic_paper_cli.py --topics "geophysics" "remote sensing" "geochemistry"
  
  # Process a list of papers from a file
  python academic_paper_cli.py --paper-list papers.txt
  
  # Use a configuration file
  python academic_paper_cli.py --config config.yaml
  
  # Save results to a specific file
  python academic_paper_cli.py --query "deep learning" --output results.json
  
  # Use Ollama for enhanced processing
  python academic_paper_cli.py --query "AI geology" --enable-llm --ollama-model llama2:13b
  
  # Use OpenAI instead of Ollama
  python academic_paper_cli.py --query "machine learning" --enable-llm --llm-provider openai
        """
    )
    
    # Configuration
    parser.add_argument('--config', 
                       help='Path to configuration file (YAML format)')
    
    # Search options
    parser.add_argument('--query', 
                       help='Search query for ad-hoc search')
    parser.add_argument('--topics', nargs='+', 
                       help='Topics for topic-based search')
    parser.add_argument('--paper-list', 
                       help='Path to file containing paper URLs/DOIs')
    
    # Output options
    parser.add_argument('--max-results', type=int, default=50,
                       help='Maximum number of results (default: 50)')
    parser.add_argument('--output', 
                       help='Output filename for results')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate report only, don\'t save results')
    
    # Processing options
    parser.add_argument('--no-pdfs', action='store_true',
                       help='Skip PDF download')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    # LLM Enhancement options
    parser.add_argument('--enable-llm', action='store_true',
                       help='Enable LLM enhancement for metadata extraction')
    parser.add_argument('--llm-provider', choices=['ollama', 'openai'],
                       help='LLM provider to use (ollama or openai)')
    parser.add_argument('--ollama-model', 
                       help='Ollama model to use (e.g., llama2, llama2:13b, codellama)')
    parser.add_argument('--ollama-base-url', 
                       help='Ollama base URL (default: http://localhost:11434)')
    parser.add_argument('--openai-api-key', 
                       help='OpenAI API key')
    parser.add_argument('--openai-model', 
                       help='OpenAI model to use (default: gpt-4)')
    
    args = parser.parse_args()
    
    # Initialize framework
    try:
        framework = AcademicPaperFramework(args.config)
        
        # Override config if specified
        if args.no_pdfs:
            framework.config['save_pdfs'] = False
        
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Override LLM settings if specified
        if args.enable_llm:
            framework.config['enable_llm_enhancement'] = True
        
        if args.llm_provider:
            framework.config['llm_provider'] = args.llm_provider
        
        if args.ollama_model:
            framework.config['ollama_model'] = args.ollama_model
        
        if args.ollama_base_url:
            framework.config['ollama_base_url'] = args.ollama_base_url
        
        if args.openai_api_key:
            framework.config['openai_api_key'] = args.openai_api_key
        
        if args.openai_model:
            framework.config['openai_model'] = args.openai_model
        
        # Re-setup LLM client with new settings
        framework._setup_llm_client()
        
    except Exception as e:
        print(f"Error initializing framework: {e}")
        sys.exit(1)
    
    # Perform searches based on arguments
    results = []
    
    if args.query:
        print(f"🔍 Performing ad-hoc search for: {args.query}")
        results = framework.search_ad_hoc(args.query, args.max_results)
    
    elif args.topics:
        print(f"🔍 Performing topic-based search for: {args.topics}")
        max_per_topic = args.max_results // len(args.topics)
        results = framework.search_by_topics(args.topics, max_per_topic)
    
    elif args.paper_list:
        print(f"📄 Processing paper list from: {args.paper_list}")
        if not Path(args.paper_list).exists():
            print(f"❌ Paper list file not found: {args.paper_list}")
            sys.exit(1)
        results = framework.process_paper_list(args.paper_list)
    
    else:
        # Default: search for configured topics
        if framework.config.get('topics_of_interest'):
            print(f"🔍 Searching configured topics: {framework.config['topics_of_interest']}")
            results = framework.search_by_topics(framework.config['topics_of_interest'], args.max_results)
        else:
            print("❌ No search specified. Use --query, --topics, or --paper-list")
            print("💡 Use --help for usage information")
            sys.exit(1)
    
    # Process results
    if results:
        print(f"\n✅ Found {len(results)} papers")
        
        # Generate and display report
        report = framework.generate_report(results)
        print(report)
        
        # Save results if requested
        if not args.report_only:
            output_file = framework.save_results(results, args.output)
            print(f"\n💾 Results saved to: {output_file}")
        
        # Show some example results
        print("\n📋 Sample Results:")
        completed_results = [r for r in results if r.state.value == 'completed']
        for i, result in enumerate(completed_results[:5]):
            if result.metadata:
                print(f"  {i+1}. {result.metadata.title}")
                if result.metadata.authors:
                    print(f"     Authors: {', '.join(result.metadata.authors[:3])}")
                if result.metadata.doi:
                    print(f"     DOI: {result.metadata.doi}")
                if result.metadata.keywords:
                    print(f"     Keywords: {', '.join(result.metadata.keywords[:3])}")
                print()
    
    else:
        print("❌ No results found.")
        sys.exit(1)

if __name__ == "__main__":
    main() 