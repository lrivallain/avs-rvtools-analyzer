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
        self.deployment_name = None
        
        # Configure using environment variables only
        self._configure_from_env()

    def _configure_from_env(self) -> None:
        """Configure Azure OpenAI using environment variables only."""
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
                logger.info("Azure OpenAI client configured via environment variables")
            except Exception as e:
                logger.error(f"Failed to configure Azure OpenAI client via environment variables: {e}")
                self.is_configured = False
        else:
            logger.info("Azure OpenAI environment variables not found or incomplete")
            self.is_configured = False

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status."""
        return {
            "is_configured": self.is_configured,
            "deployment_name": self.deployment_name if self.is_configured else None
        }

    def get_risk_analysis_suggestion(
        self, 
        risk_name: str, 
        risk_description: str, 
        risk_data: List[Dict[str, Any]], 
        risk_level: str
    ) -> Optional[str]:
        """
        Get AI-powered suggestions for a specific risk.
        
        Args:
            risk_name: Name of the risk (e.g., "detect_vusb_devices")
            risk_description: Description of the risk
            risk_data: List of risk data items
            risk_level: Risk severity level
            
        Returns:
            str: AI-generated suggestion or None if failed
        """
        if not self.is_configured or not self.client:
            logger.warning("Azure OpenAI client not configured via environment variables")
            return None

        model_name = self.deployment_name

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
## Azure VMware Solution Migration Risk Analysis

**Risk Type:** {risk_name.replace('detect_', '').replace('_', ' ').title()}
**Severity Level:** {risk_level.title()}
**Description:** {risk_description}

**Detected Issues Count:** {len(risk_data)}

**Issue Details:**
{self._format_risk_data_for_prompt(sample_data)}

## Analysis Request

You are analyzing ACTUAL DETECTED ISSUES from a VMware environment scan. These are real problems that exist in the current environment and need to be addressed for Azure VMware Solution migration.

Please provide a comprehensive analysis in HTML format with the following sections:

1. **Impact Assessment**: How these specific detected issues affect Azure VMware Solution migration
2. **Recommended Actions**: Specific steps to resolve these detected issues before or during migration  
3. **Migration Strategy**: How to handle these specific items during the migration process
4. **Timeline Considerations**: When to address these issues in the migration timeline

**Important Instructions:**
- Analyze the SPECIFIC ISSUES provided in the data above
- Do not state that issues "don't apply" - these are confirmed detected problems
- Provide actionable recommendations for the actual detected items
- Generate HTML markup directly (no markdown)
- Use heading levels h5 and below only (h5, h6)
- Include proper HTML tags for paragraphs, lists, and emphasis
- Be specific to the detected issues and Azure VMware Solution requirements
- Do not include HTML document structure tags (html, head, body)
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
        logger.debug(f"Formatting risk data: received {len(risk_data) if risk_data else 0} items")
        logger.debug(f"Risk data sample for prompt: {risk_data[:2] if risk_data and len(risk_data) > 0 else 'Empty or None'}")
        
        if not risk_data:
            return "No specific data items available for this risk."
        
        formatted_items = []
        for i, item in enumerate(risk_data, 1):
            # Convert each item to a readable format
            item_details = []
            for key, value in item.items():
                if value is not None and str(value).strip():
                    # Make key names more readable
                    readable_key = key.replace('_', ' ').title()
                    item_details.append(f"{readable_key}: {value}")
            
            if item_details:
                formatted_items.append(f"Issue {i}: {', '.join(item_details)}")
            else:
                formatted_items.append(f"Issue {i}: No detailed information available")
        
        # Add context about the data
        result = f"Analyzing {len(risk_data)} detected issues:\n\n"
        result += '\n'.join(formatted_items)
        result += f"\n\nPlease analyze these specific issues and provide recommendations tailored to addressing each type of problem found."
        
        logger.debug(f"Formatted prompt length: {len(result)} characters")
        
        return result

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Azure OpenAI connection using environment variable configuration.
        
        Returns:
            dict: Test result with success status and message
        """
        if not self.is_configured or not self.client:
            return {
                "success": False,
                "message": "Azure OpenAI not configured via environment variables"
            }
            
        try:
            # Make a simple test call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
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
                "message": "Connection test successful (using environment variables)",
                "response": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "response": None
            }