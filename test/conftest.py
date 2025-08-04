"""
Pytest configuration and shared fixtures
"""
import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def clear_environment():
    """Clear environment variables before each test"""
    # Save original environment
    original_env = os.environ.copy()

    # Clear specific environment variables
    env_vars_to_clear = ["OPENAI_API_KEY", "QWEN_API_KEY", "OLLAMA_BASE_URL"]

    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    with patch("providers.openai.openai") as mock:
        mock_client = mock.OpenAI.return_value
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices = [mock.MagicMock()]
        mock_response.choices[0].message.content = "Mocked OpenAI response"
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch("providers.requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Mocked response"}}]
        }
        yield mock_post


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing"""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What's the weather like?"},
    ]
