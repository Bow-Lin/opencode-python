"""
Model provider manager for handling multiple providers.
"""

from typing import Any, Dict, Optional

from .base import BaseProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .qwen import QwenProvider


class ProviderManager:
    """Manager for handling multiple model providers."""

    def __init__(self):
        """Initialize the provider manager."""
        self.providers: Dict[str, BaseProvider] = {}
        self.default_provider: Optional[str] = None

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """
        Register a provider with a name.

        Args:
            name: Provider name
            provider: Provider instance
        """
        self.providers[name] = provider
        if not self.default_provider:
            self.default_provider = name

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """
        Get a provider by name.

        Args:
            name: Provider name (uses default if None)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_name = name or self.default_provider
        if not provider_name:
            raise ValueError("No default provider set")

        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        return self.providers[provider_name]

    def list_providers(self) -> list:
        """
        List all registered providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def get_available_providers(self) -> list:
        """
        Get list of available (working) providers.

        Returns:
            List of available provider names
        """
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        return available

    def set_default_provider(self, name: str) -> None:
        """
        Set the default provider.

        Args:
            name: Provider name to set as default

        Raises:
            ValueError: If provider not found
        """
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        self.default_provider = name

    def generate(
        self,
        user_query: str,
        prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate text using the specified or default provider.

        Args:
            user_query: User's input message/query
            prompt: Optional system prompt to set the model's behavior
            provider_name: Provider name (uses default if None)
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        provider = self.get_provider(provider_name)
        return provider.generate(user_query, prompt, **kwargs)

    def get_provider_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a provider.

        Args:
            name: Provider name (uses default if None)

        Returns:
            Provider information dictionary
        """
        provider = self.get_provider(name)
        return provider.get_model_info()


# Factory functions for easy provider creation
def create_ollama_provider(config: Optional[Dict[str, Any]] = None) -> OllamaProvider:
    """
    Create an Ollama provider.

    Args:
        config: Configuration dictionary

    Returns:
        OllamaProvider instance
    """
    return OllamaProvider(config)


def create_openai_provider(config: Optional[Dict[str, Any]] = None) -> OpenAIProvider:
    """
    Create an OpenAI provider.

    Args:
        config: Configuration dictionary

    Returns:
        OpenAIProvider instance
    """
    return OpenAIProvider(config)


def create_qwen_provider(config: Optional[Dict[str, Any]] = None) -> QwenProvider:
    """
    Create a Qwen provider.

    Args:
        config: Configuration dictionary

    Returns:
        QwenProvider instance
    """
    return QwenProvider(config)


def create_default_manager() -> ProviderManager:
    """
    Create a provider manager with default providers.

    Returns:
        ProviderManager with Ollama and OpenAI providers
    """
    manager = ProviderManager()

    # Register Ollama provider
    try:
        ollama_provider = create_ollama_provider()
        manager.register_provider("ollama", ollama_provider)
    except Exception:
        pass  # Ollama not available

    # Register OpenAI provider
    try:
        openai_provider = create_openai_provider()
        manager.register_provider("openai", openai_provider)
    except Exception:
        pass  # OpenAI not available

    # Register Qwen provider
    try:
        qwen_provider = create_qwen_provider()
        manager.register_provider("qwen", qwen_provider)
    except Exception:
        pass  # Qwen not available

    return manager
