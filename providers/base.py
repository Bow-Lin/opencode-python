"""
Base provider class for model providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseProvider(ABC):
    """Base class for all model providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the provider with optional configuration.

        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config or {}

    @abstractmethod
    def generate(self, user_query: str, prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate text response from the model.

        Args:
            user_query: User's input message/query
            prompt: Optional system prompt to set the model's behavior
            **kwargs: Additional arguments for generation

        Returns:
            Generated text response
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.

        Returns:
            True if the provider is available, False otherwise
        """
        raise NotImplementedError

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary containing model information
        """
        return {"provider": self.__class__.__name__, "config": self.config}
