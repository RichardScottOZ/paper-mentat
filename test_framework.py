#!/usr/bin/env python3
"""
Simple test script for the Academic Paper Search Framework
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from academic_paper_framework import AcademicPaperFramework, ProcessingState, PaperMetadata

def test_framework_initialization():
    """Test framework initialization"""
    print("🧪 Testing framework initialization...")
    
    try:
        framework = AcademicPaperFramework()
        print("✅ Framework initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Framework initialization failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n🧪 Testing configuration loading...")
    
    try:
        framework = AcademicPaperFramework("config.yaml")
        print("✅ Configuration loaded successfully")
        print(f"   Topics configured: {len(framework.config.get('topics_of_interest', []))}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_paper_list_loading():
    """Test paper list loading"""
    print("\n🧪 Testing paper list loading...")
    
    try:
        framework = AcademicPaperFramework()
        urls = framework._load_paper_list("mineral_exploration_papers.txt")
        print(f"✅ Paper list loaded successfully: {len(urls)} URLs found")
        return True
    except Exception as e:
        print(f"❌ Paper list loading failed: {e}")
        return False

def test_url_extraction():
    """Test URL extraction from text"""
    print("\n🧪 Testing URL extraction...")
    
    try:
        framework = AcademicPaperFramework()
        
        # Test text with DOIs and URLs
        test_text = """
        Some papers to test:
        10.1016/j.oregeorev.2018.12.018
        https://arxiv.org/abs/1901.01234
        https://www.researchgate.net/publication/123456789_Test_Paper
        """
        
        urls = framework._extract_urls_from_text(test_text)
        print(f"✅ URL extraction successful: {len(urls)} URLs extracted")
        for url in urls:
            print(f"   - {url}")
        return True
    except Exception as e:
        print(f"❌ URL extraction failed: {e}")
        return False

def test_metadata_creation():
    """Test metadata object creation"""
    print("\n🧪 Testing metadata creation...")
    
    try:
        metadata = PaperMetadata(
            title="Test Paper Title",
            authors=["Author 1", "Author 2"],
            doi="10.1016/j.test.2023.123456",
            abstract="This is a test abstract.",
            publication_year=2023,
            journal="Test Journal"
        )
        
        print("✅ Metadata object created successfully")
        print(f"   Title: {metadata.title}")
        print(f"   Authors: {metadata.authors}")
        print(f"   DOI: {metadata.doi}")
        return True
    except Exception as e:
        print(f"❌ Metadata creation failed: {e}")
        return False

def test_processing_result_creation():
    """Test processing result creation"""
    print("\n🧪 Testing processing result creation...")
    
    try:
        metadata = PaperMetadata(
            title="Test Paper",
            authors=["Test Author"],
            doi="10.1016/j.test.2023.123456"
        )
        
        result = ProcessingState.COMPLETED # This line was not in the original file, but should be added for completeness
        result = ProcessingResult(
            url="https://doi.org/10.1016/j.test.2023.123456",
            state=ProcessingState.COMPLETED,
            metadata=metadata,
            processing_time=1.5
        )
        
        print("✅ Processing result created successfully")
        print(f"   State: {result.state.value}")
        print(f"   Processing time: {result.processing_time}s")
        return True
    except Exception as e:
        print(f"❌ Processing result creation failed: {e}")
        return False

def test_simple_search():
    """Test a simple search (limited to avoid rate limiting)"""
    print("\n🧪 Testing simple search...")
    
    try:
        framework = AcademicPaperFramework()
        
        # Test with a very specific query to get fewer results
        results = framework.search_ad_hoc("machine learning mineral exploration", max_results=5)
        
        print(f"✅ Search completed: {len(results)} results found")
        
        if results:
            print("   Sample results:")
            for i, result in enumerate(results[:2]):
                if result.metadata:
                    print(f"     {i+1}. {result.metadata.title}")
        
        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        print("   This might be due to network issues or rate limiting")
        return False

def test_report_generation():
    """Test report generation"""
    print("\n🧪 Testing report generation...")
    
    try:
        framework = AcademicPaperFramework()
        
        # Create some test results
        test_results = []
        for i in range(3):
            metadata = PaperMetadata(
                title=f"Test Paper {i+1}",
                authors=[f"Author {i+1}"],
                doi=f"10.1016/j.test.2023.{123456+i}"
            )
            
            result = ProcessingState.COMPLETED # This line was not in the original file, but should be added for completeness
            result = ProcessingResult(
                url=f"https://doi.org/10.1016/j.test.2023.{123456+i}",
                state=ProcessingState.COMPLETED,
                metadata=metadata,
                processing_time=1.0
            )
            test_results.append(result)
        
        # Generate report
        report = framework.generate_report(test_results)
        print("✅ Report generated successfully")
        print("   Report preview:")
        print(report[:200] + "...")
        
        return True
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Academic Paper Search Framework - Test Suite")
    print("=" * 50)
    
    tests = [
        test_framework_initialization,
        test_config_loading,
        test_paper_list_loading,
        test_url_extraction,
        test_metadata_creation,
        test_processing_result_creation,
        test_report_generation,
        test_simple_search
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Framework is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 