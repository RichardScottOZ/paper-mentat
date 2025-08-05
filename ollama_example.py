#!/usr/bin/env python3
"""
Example script demonstrating Ollama integration with the Academic Paper Search Framework
"""

from academic_paper_framework import AcademicPaperFramework
import json
import time

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    print("🔍 Testing Ollama connection...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running! Available models: {[m['name'] for m in models]}")
            return True
        else:
            print("❌ Ollama is not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("💡 Make sure Ollama is installed and running:")
        print("   1. Install Ollama from https://ollama.ai/")
        print("   2. Run: ollama serve")
        print("   3. Pull a model: ollama pull llama2")
        return False

def example_ollama_enhanced_search():
    """Example: Search with Ollama-enhanced metadata extraction"""
    print("\n🤖 Example: Ollama-Enhanced Search")
    print("=" * 50)
    
    # Test Ollama connection first
    if not test_ollama_connection():
        print("Skipping Ollama example due to connection issues")
        return
    
    # Initialize framework with Ollama enabled
    config = {
        'enable_llm_enhancement': True,
        'llm_provider': 'ollama',
        'ollama_model': 'llama2',
        'ollama_base_url': 'http://localhost:11434',
        'ollama_timeout': 30
    }
    
    framework = AcademicPaperFramework()
    framework.config.update(config)
    framework._setup_llm_client()
    
    # Search for papers
    print("Searching for papers with Ollama enhancement...")
    results = framework.search_ad_hoc("machine learning mineral exploration", max_results=5)
    
    # Display enhanced results
    print(f"\nFound {len(results)} papers with enhanced metadata:")
    for i, result in enumerate(results[:3]):
        if result.metadata:
            print(f"\n{i+1}. {result.metadata.title}")
            if result.metadata.authors:
                print(f"   Authors: {', '.join(result.metadata.authors)}")
            if result.metadata.doi:
                print(f"   DOI: {result.metadata.doi}")
            if result.metadata.journal:
                print(f"   Journal: {result.metadata.journal}")
            if result.metadata.publication_year:
                print(f"   Year: {result.metadata.publication_year}")
            if result.metadata.keywords:
                print(f"   Keywords: {', '.join(result.metadata.keywords)}")
            if result.metadata.abstract:
                print(f"   Abstract: {result.metadata.abstract[:200]}...")
    
    # Save results
    output_file = framework.save_results(results, "ollama_enhanced_results.json")
    print(f"\n💾 Enhanced results saved to: {output_file}")

def example_ollama_model_comparison():
    """Example: Compare different Ollama models"""
    print("\n🔄 Example: Ollama Model Comparison")
    print("=" * 50)
    
    if not test_ollama_connection():
        print("Skipping model comparison due to connection issues")
        return
    
    # Test with different models
    models_to_test = ['llama2', 'llama2:13b', 'codellama']
    available_models = []
    
    # Check which models are available
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            available_models = [m['name'] for m in models]
            print(f"Available models: {available_models}")
    except Exception as e:
        print(f"Error checking available models: {e}")
        return
    
    # Test each available model
    for model in models_to_test:
        if model in available_models:
            print(f"\n🧪 Testing model: {model}")
            
            config = {
                'enable_llm_enhancement': True,
                'llm_provider': 'ollama',
                'ollama_model': model,
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 30
            }
            
            framework = AcademicPaperFramework()
            framework.config.update(config)
            framework._setup_llm_client()
            
            # Test with a single paper
            start_time = time.time()
            results = framework.search_ad_hoc("deep learning geology", max_results=2)
            processing_time = time.time() - start_time
            
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Results found: {len(results)}")
            
            if results and results[0].metadata:
                metadata = results[0].metadata
                print(f"   Sample title: {metadata.title}")
                if metadata.keywords:
                    print(f"   Keywords extracted: {len(metadata.keywords)}")
        else:
            print(f"⚠️ Model {model} not available")

def example_ollama_paper_list_processing():
    """Example: Process paper list with Ollama enhancement"""
    print("\n📄 Example: Ollama-Enhanced Paper List Processing")
    print("=" * 50)
    
    if not test_ollama_connection():
        print("Skipping paper list processing due to connection issues")
        return
    
    # Initialize framework with Ollama
    config = {
        'enable_llm_enhancement': True,
        'llm_provider': 'ollama',
        'ollama_model': 'llama2',
        'ollama_base_url': 'http://localhost:11434',
        'ollama_timeout': 30
    }
    
    framework = AcademicPaperFramework()
    framework.config.update(config)
    framework._setup_llm_client()
    
    # Process paper list
    print("Processing paper list with Ollama enhancement...")
    results = framework.process_paper_list("mineral_exploration_papers.txt")
    
    # Analyze results
    successful = [r for r in results if r.state.value == 'completed']
    failed = [r for r in results if r.state.value == 'failed']
    
    print(f"\nProcessing Results:")
    print(f"  Total papers: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    
    # Show enhanced metadata examples
    print(f"\nEnhanced Metadata Examples:")
    for i, result in enumerate(successful[:3]):
        if result.metadata:
            print(f"\n{i+1}. {result.metadata.title}")
            if result.metadata.journal:
                print(f"   Journal: {result.metadata.journal}")
            if result.metadata.publication_year:
                print(f"   Year: {result.metadata.publication_year}")
            if result.metadata.keywords:
                print(f"   Keywords: {', '.join(result.metadata.keywords[:5])}")
    
    # Save results
    output_file = framework.save_results(results, "ollama_paper_list_results.json")
    print(f"\n💾 Enhanced results saved to: {output_file}")

def example_ollama_config_file():
    """Example: Use configuration file with Ollama settings"""
    print("\n⚙️ Example: Configuration File with Ollama")
    print("=" * 50)
    
    if not test_ollama_connection():
        print("Skipping config file example due to connection issues")
        return
    
    # Create a temporary config file with Ollama settings
    temp_config = {
        'enable_llm_enhancement': True,
        'llm_provider': 'ollama',
        'ollama_model': 'llama2',
        'ollama_base_url': 'http://localhost:11434',
        'ollama_timeout': 30,
        'topics_of_interest': ['machine learning geology', 'AI mineral exploration'],
        'max_results': 3
    }
    
    # Save temporary config
    import yaml
    with open('temp_ollama_config.yaml', 'w') as f:
        yaml.dump(temp_config, f)
    
    try:
        # Use the config file
        framework = AcademicPaperFramework('temp_ollama_config.yaml')
        
        print("Searching with Ollama-enhanced configuration...")
        results = framework.search_by_topics(['machine learning geology'], max_results_per_topic=2)
        
        print(f"\nFound {len(results)} papers with Ollama enhancement")
        
        # Show results
        for i, result in enumerate(results[:2]):
            if result.metadata:
                print(f"\n{i+1}. {result.metadata.title}")
                if result.metadata.keywords:
                    print(f"   Keywords: {', '.join(result.metadata.keywords)}")
        
        # Save results
        output_file = framework.save_results(results, "ollama_config_results.json")
        print(f"\n💾 Results saved to: {output_file}")
        
    finally:
        # Clean up temporary config
        import os
        if os.path.exists('temp_ollama_config.yaml'):
            os.remove('temp_ollama_config.yaml')

def main():
    """Run all Ollama examples"""
    print("Academic Paper Search Framework - Ollama Integration Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_ollama_enhanced_search()
        example_ollama_model_comparison()
        example_ollama_paper_list_processing()
        example_ollama_config_file()
        
        print("\n✅ All Ollama examples completed successfully!")
        print("\n📁 Check the 'results' directory for enhanced JSON files")
        print("\n💡 Tips for using Ollama:")
        print("   - Install Ollama from https://ollama.ai/")
        print("   - Run: ollama serve")
        print("   - Pull models: ollama pull llama2")
        print("   - Use different models: ollama pull codellama")
        
    except Exception as e:
        print(f"\n❌ Error running Ollama examples: {e}")
        print("Make sure Ollama is installed and running:")
        print("1. Install Ollama from https://ollama.ai/")
        print("2. Run: ollama serve")
        print("3. Pull a model: ollama pull llama2")

if __name__ == "__main__":
    main() 