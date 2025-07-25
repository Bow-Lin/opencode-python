"""
OpenAI model provider implementation.
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .base import BaseProvider

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """OpenAI model provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OpenAI provider.

        Args:
            config: Configuration dictionary with keys:
                - api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
                - model: Model name to use (default: gpt-3.5-turbo)
                - base_url: Custom API base URL (optional)
        """
        load_dotenv()
        default_config = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-3.5-turbo",
            "base_url": None,
        }
        if config:
            default_config.update(config)
        super().__init__(default_config)

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. " "Install with: pip install openai"
            )

        # Configure OpenAI client
        if self.config["api_key"]:
            openai.api_key = self.config["api_key"]
            if self.config["base_url"]:
                openai.base_url = self.config["base_url"]

    def is_available(self) -> bool:
        """
        Check if OpenAI is available and properly configured.

        Returns:
            True if OpenAI is available, False otherwise
        """
        if not OPENAI_AVAILABLE:
            return False

        if not self.config["api_key"]:
            return False

        try:
            # Test with a simple request
            openai.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False

    def generate(self, user_query: str, prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using OpenAI API.

        Args:
            user_query: User's input message/query
            prompt: Optional system prompt to set the model's behavior
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            RuntimeError: If OpenAI is not available or request fails
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "OpenAI package not installed. " "Install with: pip install openai"
            )

        if not self.config["api_key"]:
            raise RuntimeError(
                "OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable or pass api_key in "
                "config."
            )

        if not self.is_available():
            raise RuntimeError(
                "OpenAI is not available. "
                "Please check your API key and configuration."
            )

        # Prepare messages
        messages = []
        if prompt:
            messages.append({"role": "system", "content": prompt})
        messages.append({"role": "user", "content": user_query})

        # Prepare generation parameters
        generation_params = {
            "model": self.config["model"],
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        }

        try:
            response = openai.chat.completions.create(**generation_params)
            return response.choices[0].message.content or ""

        except Exception as e:
            raise RuntimeError(f"Failed to generate text with OpenAI: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary containing model information
        """
        info = super().get_model_info()
        info.update(
            {
                "model": self.config["model"],
                "has_api_key": bool(self.config["api_key"]),
                "base_url": self.config["base_url"],
            }
        )
        return info
