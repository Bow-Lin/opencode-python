"""
Ollama model provider implementation.
"""

from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama model provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ollama provider.

        Args:
            config: Configuration dictionary with keys:
                - base_url: Ollama API base URL (default: http://localhost:11434)
                - model: Model name to use (default: llama2)
                - timeout: Request timeout in seconds (default: 30)
        """
        load_dotenv()
        default_config = {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "timeout": 30,
        }
        if config:
            default_config.update(config)
        super().__init__(default_config)

    def is_available(self) -> bool:
        """
        Check if Ollama is available and running.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.config['base_url']}/api/tags", timeout=self.config["timeout"]
            )
            return response.status_code == 200
        except (requests.RequestException, Exception):
            return False

    def generate(self, user_query: str, prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using Ollama API.

        Args:
            user_query: User's input message/query
            prompt: Optional system prompt to set the model's behavior
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            requests.RequestException: If the API request fails
        """
        if not self.is_available():
            raise RuntimeError(
                "Ollama is not available. Please ensure Ollama is running."
            )

        # Prepare the full prompt with system prompt if provided
        full_prompt_text = user_query
        if prompt:
            full_prompt_text = f"{prompt}\n\n{user_query}"

        # Prepare the request payload
        payload = {
            "model": self.config["model"],
            "prompt": full_prompt_text,
            "stream": False,
        }

        # Add additional parameters from kwargs
        for key, value in kwargs.items():
            if key in ["temperature", "top_p", "top_k", "repeat_penalty"]:
                payload[key] = value

        try:
            response = requests.post(
                f"{self.config['base_url']}/api/generate",
                json=payload,
                timeout=self.config["timeout"],
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate text with Ollama: {e}")

    def list_models(self) -> list:
        """
        List available models in Ollama.

        Returns:
            List of available model names
        """
        try:
            response = requests.get(
                f"{self.config['base_url']}/api/tags", timeout=self.config["timeout"]
            )
            response.raise_for_status()

            result = response.json()
            return [model["name"] for model in result.get("models", [])]

        except requests.RequestException:
            return []

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary containing model information
        """
        info = super().get_model_info()
        info.update(
            {
                "base_url": self.config["base_url"],
                "model": self.config["model"],
                "available_models": self.list_models(),
            }
        )
        return info
