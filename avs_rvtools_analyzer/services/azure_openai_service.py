"""
Azure OpenAI service for generating risk analysis suggestions.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Service for handling Azure OpenAI API calls for risk analysis suggestions."""

    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self.is_configured = False
        self.configured_via_env = False
        self.deployment_name = None
        
        # Check for environment variables on initialization
        self._check_env_configuration()

    def _check_env_configuration(self) -> None:
        """Check if Azure OpenAI is configured via environment variables."""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        if azure_endpoint and api_key and deployment_name:
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=api_key,
                    api_version="2024-02-01"
                )
                self.deployment_name = deployment_name
                self.is_configured = True
                self.configured_via_env = True
                logger.info("Azure OpenAI client configured via environment variables")
            except Exception as e:
                logger.error(f"Failed to configure Azure OpenAI client via environment variables: {e}")
                self.is_configured = False
                self.configured_via_env = False

    def is_configured_via_env(self) -> bool:
        """Check if the service is configured via environment variables."""
        return self.configured_via_env

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status."""
        return {
            "is_configured": self.is_configured,
            "configured_via_env": self.configured_via_env,
            "deployment_name": self.deployment_name if self.configured_via_env else None
        }

    def configure(self, azure_endpoint: str, api_key: str, api_version: str = "2024-02-01") -> bool:
        """
        Configure the Azure OpenAI client.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: OpenAI API key
            api_version: API version to use
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        # Don't allow reconfiguration if already configured via env vars
        if self.configured_via_env:
            logger.warning("Azure OpenAI is already configured via environment variables")
            return True
            
        try:
            self.client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            self.is_configured = True
            logger.info("Azure OpenAI client configured successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Azure OpenAI client: {e}")
            self.is_configured = False
            return False

    def get_risk_analysis_suggestion(
        self, 
        risk_name: str, 
        risk_description: str, 
        risk_data: List[Dict[str, Any]], 
        risk_level: str,
        deployment_name: str = "gpt-4"
    ) -> Optional[str]:
        """
        Get AI-powered suggestions for a specific risk.
        
        Args:
            risk_name: Name of the risk (e.g., "detect_vusb_devices")
            risk_description: Description of the risk
            risk_data: List of risk data items
            risk_level: Risk severity level
            deployment_name: Azure OpenAI deployment name (ignored if configured via env vars)
            
        Returns:
            str: AI-generated suggestion or None if failed
        """
        if not self.is_configured or not self.client:
            logger.warning("Azure OpenAI client not configured")
            return None

        # Use env deployment name if configured via env vars, otherwise use provided one
        model_name = self.deployment_name if self.configured_via_env else deployment_name

        try:
            # Prepare the prompt
            prompt = self._build_risk_analysis_prompt(
                risk_name, risk_description, risk_data, risk_level
            )
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Azure VMware Solution migration consultant. Provide practical, actionable recommendations for addressing migration risks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            suggestion = response.choices[0].message.content
            logger.info(f"Generated suggestion for risk: {risk_name}")
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to get AI suggestion for {risk_name}: {e}")
            return None

    def _build_risk_analysis_prompt(
        self, 
        risk_name: str, 
        risk_description: str, 
        risk_data: List[Dict[str, Any]], 
        risk_level: str
    ) -> str:
        """
        Build a comprehensive prompt for risk analysis.
        
        Args:
            risk_name: Name of the risk
            risk_description: Description of the risk
            risk_data: List of risk data items
            risk_level: Risk severity level
            
        Returns:
            str: Formatted prompt for AI analysis
        """
        # Limit data to prevent token overflow
        sample_data = risk_data[:10] if len(risk_data) > 10 else risk_data
        
        prompt = f"""
## Migration Risk Analysis Request

**Risk Type:** {risk_name.replace('detect_', '').replace('_', ' ').title()}
**Severity Level:** {risk_level.title()}
**Description:** {risk_description}

**Detected Issues Count:** {len(risk_data)}

**Sample Data (first 10 items):**
{self._format_risk_data_for_prompt(sample_data)}

## Request
Please provide a comprehensive analysis in HTML format with the following sections:
1. **Impact Assessment**: How this risk affects Azure VMware Solution migration
2. **Recommended Actions**: Specific steps to mitigate this risk
3. **Migration Strategy**: How to handle these items during migration
4. **Timeline Considerations**: When to address this risk in the migration process

**Output Requirements:**
- Generate HTML markup directly (no markdown)
- Use heading levels h5 and below only (h5, h6)
- Include proper HTML tags for paragraphs, lists, and emphasis
- Be concise, practical, and specific to Azure VMware Solution migration requirements
- Do not include any HTML document structure (html, head, body tags)
"""
        return prompt

    def _format_risk_data_for_prompt(self, risk_data: List[Dict[str, Any]]) -> str:
        """
        Format risk data for inclusion in the AI prompt.
        
        Args:
            risk_data: List of risk data items
            
        Returns:
            str: Formatted data string
        """
        if not risk_data:
            return "No specific data items available."
        
        formatted_items = []
        for i, item in enumerate(risk_data, 1):
            # Convert each item to a readable format
            item_str = f"Item {i}:"
            for key, value in item.items():
                if value is not None and str(value).strip():
                    item_str += f" {key}: {value},"
            formatted_items.append(item_str.rstrip(','))
        
        return '\n'.join(formatted_items)

    def test_connection(self, azure_endpoint: str = None, api_key: str = None, deployment_name: str = "gpt-4") -> Dict[str, Any]:
        """
        Test the Azure OpenAI connection with provided credentials or environment variables.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL (ignored if configured via env vars)
            api_key: OpenAI API key (ignored if configured via env vars)
            deployment_name: Deployment name to test (ignored if configured via env vars)
            
        Returns:
            dict: Test result with success status and message
        """
        try:
            # If configured via env vars, test the existing client
            if self.configured_via_env:
                if not self.client:
                    return {
                        "success": False,
                        "message": "Azure OpenAI configured via environment variables but client not initialized"
                    }
                    
                test_client = self.client
                test_deployment = self.deployment_name
                message_suffix = " (using environment variables)"
            else:
                # Create a temporary client for testing with provided credentials
                if not azure_endpoint or not api_key:
                    return {
                        "success": False,
                        "message": "Azure endpoint and API key are required when not configured via environment variables"
                    }
                    
                test_client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=api_key,
                    api_version="2024-02-01"
                )
                test_deployment = deployment_name
                message_suffix = ""
            
            # Make a simple test call
            response = test_client.chat.completions.create(
                model=test_deployment,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a connection test. Please respond with 'Connection successful'."
                    }
                ],
                max_tokens=10,
                temperature=0
            )
            
            return {
                "success": True,
                "message": f"Connection test successful{message_suffix}",
                "response": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed{message_suffix}: {str(e)}",
                "response": None
            }