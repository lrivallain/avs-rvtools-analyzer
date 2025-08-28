#!/usr/bin/env python3
"""
Test script for Azure OpenAI integration.
This script will verify the Azure OpenAI service functionality without requiring full app setup.
"""

import json
import sys
from pathlib import Path

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

def test_azure_openai_service():
    """Test the Azure OpenAI service with mock data."""
    try:
        # Try importing our service (will fail if openai package is missing)
        from avs_rvtools_analyzer.services.azure_openai_service import AzureOpenAIService
        
        service = AzureOpenAIService()
        print("✅ AzureOpenAIService imported successfully")
        
        # Test initialization
        assert not service.is_configured, "Service should not be configured initially"
        print("✅ Service initialization test passed")
        
        # Test prompt building
        test_risk_data = [
            {"VM Name": "test-vm-1", "Device": "USB Device 1"},
            {"VM Name": "test-vm-2", "Device": "USB Device 2"}
        ]
        
        prompt = service._build_risk_analysis_prompt(
            risk_name="detect_vusb_devices",
            risk_description="vUSB devices connected to VMs",
            risk_data=test_risk_data,
            risk_level="blocking"
        )
        
        assert "detect_vusb_devices" in prompt, "Prompt should contain risk name"
        assert "blocking" in prompt.lower(), "Prompt should contain risk level"
        assert "test-vm-1" in prompt, "Prompt should contain sample data"
        print("✅ Prompt building test passed")
        
        # Test data formatting
        formatted_data = service._format_risk_data_for_prompt(test_risk_data)
        assert "Item 1:" in formatted_data, "Formatted data should contain item numbers"
        assert "USB Device 1" in formatted_data, "Formatted data should contain risk data"
        print("✅ Data formatting test passed")
        
        print("\n🎉 All Azure OpenAI service tests passed!")
        print("Note: Connection and AI suggestion tests require valid Azure OpenAI credentials")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This is expected if the 'openai' package is not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models():
    """Test the new models."""
    try:
        from avs_rvtools_analyzer.models import (
            AzureOpenAIConfigRequest,
            AISuggestionRequest,
            AISuggestionResponse,
            AzureOpenAITestResponse
        )
        
        # Test AzureOpenAIConfigRequest
        config_req = AzureOpenAIConfigRequest(
            azure_endpoint="https://test.openai.azure.com/",
            api_key="test-key"
        )
        assert config_req.deployment_name == "gpt-4", "Default deployment should be gpt-4"
        print("✅ AzureOpenAIConfigRequest test passed")
        
        # Test AISuggestionRequest
        suggestion_req = AISuggestionRequest(
            risk_name="test_risk",
            risk_description="Test description",
            risk_data=[{"test": "data"}],
            risk_level="warning",
            azure_endpoint="https://test.openai.azure.com/",
            api_key="test-key"
        )
        assert suggestion_req.risk_name == "test_risk", "Risk name should be set correctly"
        print("✅ AISuggestionRequest test passed")
        
        # Test AISuggestionResponse
        suggestion_resp = AISuggestionResponse(
            success=True,
            suggestion="Test suggestion",
            risk_name="test_risk"
        )
        assert suggestion_resp.success == True, "Success should be True"
        print("✅ AISuggestionResponse test passed")
        
        # Test AzureOpenAITestResponse
        test_resp = AzureOpenAITestResponse(
            success=True,
            message="Test successful"
        )
        assert test_resp.success == True, "Success should be True"
        print("✅ AzureOpenAITestResponse test passed")
        
        print("🎉 All model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_template_modifications():
    """Test that template modifications are correct."""
    try:
        template_path = Path("avs_rvtools_analyzer/templates/analyze.html")
        if not template_path.exists():
            print("❌ Template file not found")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Azure OpenAI configuration section
        assert "azure-openai-config" in content, "Template should contain Azure OpenAI config section"
        assert "testAzureOpenAIConnection" in content, "Template should contain test connection function"
        assert "getAISuggestion" in content, "Template should contain AI suggestion function"
        assert "ai-suggestion-btn" in content, "Template should contain AI suggestion button class"
        
        print("✅ Template modifications test passed")
        return True
        
    except Exception as e:
        print(f"❌ Template test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running Azure OpenAI integration tests...\n")
    
    success = True
    
    print("1. Testing Azure OpenAI service...")
    success &= test_azure_openai_service()
    
    print("\n2. Testing models...")
    success &= test_models()
    
    print("\n3. Testing template modifications...")
    success &= test_template_modifications()
    
    if success:
        print("\n🎉 All tests passed! The Azure OpenAI integration is ready.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)