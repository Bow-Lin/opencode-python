"""
Qwen model provider implementation using Alibaba Cloud DashScope API.
"""

import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .base import BaseProvider


class QwenProvider(BaseProvider):
    """Qwen model provider using DashScope API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Qwen provider.

        Args:
            config: Configuration dictionary with keys:
                - api_key: DashScope API key (default: from DASHSCOPE_API_KEY env var)
                - model: Model name to use (default: qwen-turbo)
                - base_url: API base URL (default: https://dashscope.aliyuncs.com/
                  compatible-mode/v1)
                - timeout: Request timeout in seconds (default: 30)
        """
        load_dotenv()
        default_config = {
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "model": "qwen-turbo",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "timeout": 30,
        }
        if config:
            default_config.update(config)
        super().__init__(default_config)

    def is_available(self) -> bool:
        """
        Check if Qwen provider is available and properly configured.

        Returns:
            True if Qwen is available, False otherwise
        """
        if not self.config["api_key"]:
            return False

        try:
            # Test with a simple request
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.config["model"],
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
            }

            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config["timeout"],
            )
            return response.status_code == 200

        except Exception:
            return False

    def generate(self, user_query: str, prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using Qwen API.

        Args:
            user_query: User's input message/query
            prompt: Optional system prompt to set the model's behavior
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Qwen is not available or request fails
        """
        if not self.config["api_key"]:
            raise RuntimeError(
                "DashScope API key not configured. "
                "Set DASHSCOPE_API_KEY environment variable or pass api_key in "
                "config."
            )

        if not self.is_available():
            raise RuntimeError(
                "Qwen is not available. " "Please check your API key and configuration."
            )

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

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

        # Remove None values
        generation_params = {
            k: v for k, v in generation_params.items() if v is not None
        }

        try:
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                json=generation_params,
                timeout=self.config["timeout"],
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate text with Qwen: {e}")
        except KeyError as e:
            raise RuntimeError(f"Unexpected response format from Qwen API: {e}")

    def list_models(self) -> list:
        """
        List available Qwen models.

        Returns:
            List of available model names
        """
        # Common Qwen models available through DashScope
        return [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-longcontext",
            "qwen-vl-plus",
            "qwen-vl-max",
        ]

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
                "available_models": self.list_models(),
            }
        )
        return info
