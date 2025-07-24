"""
Base provider class for model providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


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
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response from the model.
        
        Args:
            prompt: Input prompt for the model
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
        return {
            "provider": self.__class__.__name__,
            "config": self.config
        } 