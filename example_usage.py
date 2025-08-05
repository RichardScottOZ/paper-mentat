#!/usr/bin/env python3
"""
Example usage of the Academic Paper Search Framework
Demonstrates how to use the framework programmatically
"""

from academic_paper_framework import AcademicPaperFramework
import json

def example_ad_hoc_search():
    """Example: Perform an ad-hoc search"""
    print("🔍 Example 1: Ad-hoc Search")
    print("=" * 50)
    
    # Initialize framework
    framework = AcademicPaperFramework()
    
    # Search for papers
    results = framework.search_ad_hoc("machine learning mineral exploration", max_results=10)
    
    # Display results
    print(f"Found {len(results)} papers")
    for i, result in enumerate(results[:3]):
        if result.metadata:
            print(f"\n{i+1}. {result.metadata.title}")
            if result.metadata.authors:
                print(f"   Authors: {', '.join(result.metadata.authors[:2])}")
            if result.metadata.doi:
                print(f"   DOI: {result.metadata.doi}")
    
    # Save results
    output_file = framework.save_results(results, "ad_hoc_search_results.json")
    print(f"\nResults saved to: {output_file}")
    
    # Generate report
    report = framework.generate_report(results)
    print("\nReport:")
    print(report)

def example_topic_search():
    """Example: Search multiple topics"""
    print("\n🔍 Example 2: Topic-based Search")
    print("=" * 50)
    
    # Initialize framework
    framework = AcademicPaperFramework()
    
    # Define topics
    topics = ["geophysics", "remote sensing", "geochemistry"]
    
    # Search for papers
    results = framework.search_by_topics(topics, max_results_per_topic=5)
    
    # Display results
    print(f"Found {len(results)} papers across {len(topics)} topics")
    
    # Group by topic
    topic_results = {}
    for result in results:
        if result.metadata and result.metadata.title:
            # Simple topic detection (in a real scenario, you'd use more sophisticated methods)
            for topic in topics:
                if topic.lower() in result.metadata.title.lower():
                    if topic not in topic_results:
                        topic_results[topic] = []
                    topic_results[topic].append(result)
                    break
    
    for topic, topic_papers in topic_results.items():
        print(f"\n{topic.upper()} papers:")
        for i, paper in enumerate(topic_papers[:2]):
            print(f"  {i+1}. {paper.metadata.title}")
    
    # Save results
    output_file = framework.save_results(results, "topic_search_results.json")
    print(f"\nResults saved to: {output_file}")

def example_paper_list_processing():
    """Example: Process a paper list"""
    print("\n📄 Example 3: Paper List Processing")
    print("=" * 50)
    
    # Initialize framework
    framework = AcademicPaperFramework()
    
    # Process paper list
    results = framework.process_paper_list("mineral_exploration_papers.txt")
    
    # Display results
    print(f"Processed {len(results)} papers from list")
    
    # Show successful vs failed
    successful = [r for r in results if r.state.value == 'completed']
    failed = [r for r in results if r.state.value == 'failed']
    
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    # Show some successful results
    print("\nSuccessful papers:")
    for i, result in enumerate(successful[:3]):
        if result.metadata:
            print(f"  {i+1}. {result.metadata.title}")
            if result.metadata.doi:
                print(f"     DOI: {result.metadata.doi}")
    
    # Save results
    output_file = framework.save_results(results, "paper_list_results.json")
    print(f"\nResults saved to: {output_file}")

def example_configuration_usage():
    """Example: Use configuration file"""
    print("\n⚙️ Example 4: Configuration-based Search")
    print("=" * 50)
    
    # Initialize framework with config
    framework = AcademicPaperFramework("config.yaml")
    
    # Search using configured topics
    if framework.config.get('topics_of_interest'):
        results = framework.search_by_topics(
            framework.config['topics_of_interest'][:3],  # Use first 3 topics
            max_results_per_topic=3
        )
        
        print(f"Found {len(results)} papers using configured topics")
        
        # Show results by topic
        for topic in framework.config['topics_of_interest'][:3]:
            topic_papers = [r for r in results if r.metadata and topic.lower() in r.metadata.title.lower()]
            print(f"\n{topic}: {len(topic_papers)} papers")
            for paper in topic_papers[:2]:
                print(f"  - {paper.metadata.title}")
        
        # Save results
        output_file = framework.save_results(results, "config_search_results.json")
        print(f"\nResults saved to: {output_file}")
    else:
        print("No topics configured in config.yaml")

def example_advanced_usage():
    """Example: Advanced usage with custom processing"""
    print("\n🚀 Example 5: Advanced Usage")
    print("=" * 50)
    
    # Initialize framework
    framework = AcademicPaperFramework()
    
    # Custom search with specific parameters
    query = "deep learning geology"
    results = framework.search_ad_hoc(query, max_results=20)
    
    # Custom analysis
    print(f"Search query: {query}")
    print(f"Total papers found: {len(results)}")
    
    # Analyze by year (if available)
    papers_by_year = {}
    for result in results:
        if result.metadata and result.metadata.publication_year:
            year = result.metadata.publication_year
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(result)
    
    if papers_by_year:
        print("\nPapers by year:")
        for year in sorted(papers_by_year.keys(), reverse=True):
            print(f"  {year}: {len(papers_by_year[year])} papers")
    
    # Analyze by journal
    journals = {}
    for result in results:
        if result.metadata and result.metadata.journal:
            journal = result.metadata.journal
            journals[journal] = journals.get(journal, 0) + 1
    
    if journals:
        print("\nTop journals:")
        for journal, count in sorted(journals.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {journal}: {count} papers")
    
    # Save detailed results
    output_file = framework.save_results(results, "advanced_search_results.json")
    print(f"\nDetailed results saved to: {output_file}")

def main():
    """Run all examples"""
    print("Academic Paper Search Framework - Usage Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_ad_hoc_search()
        example_topic_search()
        example_paper_list_processing()
        example_configuration_usage()
        example_advanced_usage()
        
        print("\n✅ All examples completed successfully!")
        print("\n📁 Check the 'results' directory for downloaded PDFs and JSON files")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main() 