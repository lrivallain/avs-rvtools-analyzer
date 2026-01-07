"""
Azure OpenAI service for generating risk analysis suggestions.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import importlib.resources as resources

from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Service for handling Azure OpenAI API calls for risk analysis suggestions."""

    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self.is_configured = False
        self.deployment_name = None
        self.max_tokens = self._get_max_tokens_config()

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
                    api_version="2024-02-01",
                )
                self.deployment_name = deployment_name
                self.is_configured = True
                logger.info("Azure OpenAI client configured via environment variables")
            except Exception as e:
                logger.error(
                    f"Failed to configure Azure OpenAI client via environment variables: {e}"
                )
                self.is_configured = False
        else:
            logger.info("Azure OpenAI environment variables not found or incomplete")
            self.is_configured = False

    def _get_max_tokens_config(self) -> int:
        """
        Get max tokens configuration from environment variable.

        Returns:
            int: Max tokens value (default 2000 for better completeness)
        """
        try:
            env_value = os.getenv("AZURE_OPENAI_MAX_TOKENS", "500")
            max_tokens = int(env_value)

            logger.info("Using max_tokens configuration: %s", max_tokens)
            return max_tokens

        except (ValueError, TypeError):
            logger.warning("Invalid AZURE_OPENAI_MAX_TOKENS value, using default 2000")
            return 2000

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status."""
        return {
            "is_configured": self.is_configured,
            "deployment_name": self.deployment_name if self.is_configured else None,
            "max_tokens": self.max_tokens,
        }

    def get_risk_analysis_suggestion(
        self,
        risk_name: str,
        risk_description: str,
        risk_data: List[Dict[str, Any]],
        risk_level: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI-powered suggestions for a specific risk.

        Args:
            risk_name: Name of the risk (e.g., "detect_vusb_devices")
            risk_description: Description of the risk
            risk_data: List of risk data items
            risk_level: Risk severity level

        Returns:
            dict: AI-generated suggestion with token usage or None if failed
                  Format: {"suggestion": str, "tokens_used": int}
        """
        if not self.is_configured or not self.client:
            logger.warning(
                "Azure OpenAI client not configured via environment variables"
            )
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
                        "content": "You are an expert Azure VMware Solution migration consultant. Provide practical, actionable recommendations for addressing migration risks.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )

            suggestion = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            carbon_footprint = self._calculate_carbon_footprint(tokens_used)
            logger.info(
                "Generated suggestion for risk: %s (tokens used: %s, carbon footprint: %s)",
                risk_name,
                tokens_used,
                carbon_footprint,
            )

            return {
                "suggestion": suggestion,
                "tokens_used": tokens_used,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "carbon_footprint": carbon_footprint,
            }

        except Exception as e:
            logger.error("Failed to get AI suggestion for %s: %s", risk_name, e)
            return None

    def _build_risk_analysis_prompt(
        self,
        risk_name: str,
        risk_description: str,
        risk_data: List[Dict[str, Any]],
        risk_level: str,
    ) -> str:
        """
        Build the risk analysis prompt from an external markdown template.

        Args:
            risk_name: Name of the risk
            risk_description: Description of the risk
            risk_data: List of risk data items
            risk_level: Risk severity level

        Returns:
            str: Formatted prompt for AI analysis
        """
        sample_data = risk_data[:10] if len(risk_data) > 10 else risk_data
        word_limits = self._calculate_word_limits()

        # Load template from package resources, fallback to inline if unavailable
        template = self._load_prompt_template()

        formatted_prompt = template.format(
            risk_type=risk_name.replace("detect_", "").replace("_", " ").title(),
            risk_level=risk_level.title(),
            risk_description=risk_description,
            issues_count=len(risk_data),
            issues_details=self._format_risk_data_for_prompt(sample_data),
            total_words=word_limits["total"],
            impact_words=word_limits["impact"],
            actions_words=word_limits["actions"],
            strategy_words=word_limits["strategy"],
            timeline_words=word_limits["timeline"],
        )

        return formatted_prompt

    def _load_prompt_template(self) -> str:
        """Load the risk analysis prompt template from package resources.

        Returns:
            The template string with format placeholders.
        """
        with resources.files("avs_rvtools_analyzer.prompts").joinpath(
            "risk_analysis_prompt.md"
        ).open("r", encoding="utf-8") as f:
            template = f.read()
            logger.debug("Loaded risk analysis prompt template from package.")
            return template

    def _calculate_word_limits(self) -> Dict[str, int]:
        """
        Calculate word limits for each section based on max_tokens configuration.
        Since max_tokens only limits output, we can use the full allocation for response.

        Returns:
            dict: Word limits for each section
        """
        # Conservative estimation: 1 token ≈ 0.75 words
        # Use full max_tokens allocation for output since it doesn't count input
        estimated_words = int(self.max_tokens * 0.75)

        # Distribute words across sections with reasonable proportions
        total_words = estimated_words
        impact_words = int(total_words * 0.25)  # 25%
        actions_words = int(total_words * 0.375)  # 37.5%
        strategy_words = int(total_words * 0.25)  # 25%
        timeline_words = int(total_words * 0.125)  # 12.5%

        return {
            "total": total_words,
            "impact": impact_words,
            "actions": actions_words,
            "strategy": strategy_words,
            "timeline": timeline_words,
        }

    def _format_risk_data_for_prompt(self, risk_data: List[Dict[str, Any]]) -> str:
        """
        Format risk data for inclusion in the AI prompt.

        Args:
            risk_data: List of risk data items

        Returns:
            str: Formatted data string
        """
        logger.debug(
            "Formatting risk data: received %s items",
            len(risk_data) if risk_data else 0,
        )
        logger.debug(
            "Risk data sample for prompt: %s",
            risk_data[:2] if risk_data and len(risk_data) > 0 else "Empty or None",
        )

        if not risk_data:
            return "No specific data items available for this risk."

        formatted_items = []
        for i, item in enumerate(risk_data, 1):
            # Convert each item to a readable format
            item_details = []
            for key, value in item.items():
                if value is not None and str(value).strip():
                    # Make key names more readable
                    readable_key = key.replace("_", " ").title()
                    item_details.append(f"{readable_key}: {value}")

            if item_details:
                formatted_items.append(f"Issue {i}: {', '.join(item_details)}")
            else:
                formatted_items.append(f"Issue {i}: No detailed information available")

        # Add context about the data
        result = "Analyzing {} detected issues:\n\n".format(len(risk_data))
        result += "\n".join(formatted_items)
        result += "\n\nPlease analyze these specific issues and provide recommendations tailored to addressing each type of problem found."

        logger.debug("Formatted prompt length: %s characters", len(result))

        return result

    def _calculate_carbon_footprint(self, tokens: int) -> float:
        """
        Calculate carbon footprint estimation for AI inference.

        Args:
            tokens: Number of tokens used

        Returns:
            float: Carbon footprint in grams CO2e
        """
        # Carbon footprint estimation for AI inference
        # Based on industry estimates:
        # - GPT-4 class models: ~0.0047 grams CO2e per 1000 tokens
        # - This includes data center electricity, cooling, and infrastructure
        # - Assumes average grid carbon intensity and modern data centers

        grams_per_thousand_tokens = 0.0047  # grams CO2e per 1000 tokens
        total_grams = (tokens / 1000) * grams_per_thousand_tokens

        return round(total_grams, 3)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Azure OpenAI connection using environment variable configuration.

        Returns:
            dict: Test result with success status and message
        """
        if not self.is_configured or not self.client:
            return {
                "success": False,
                "message": "Azure OpenAI not configured via environment variables",
            }

        try:
            # Make a simple test call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a connection test. Please respond with 'Connection successful'.",
                    }
                ],
                max_tokens=10,
                temperature=0,
            )

            return {
                "success": True,
                "message": "Connection test successful (using environment variables)",
                "response": response.choices[0].message.content,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "response": None,
            }
