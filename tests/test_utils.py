"""
Test utilities for AXE test suite.
Provides common helper functions for testing.
"""
from unittest.mock import MagicMock


def create_mock_openai_client_without_responses():
    """
    Create a mock OpenAI client without responses API support.
    
    This simulates an older OpenAI SDK version that doesn't have
    the Responses API (versions before 1.58.0).
    
    Returns:
        MagicMock: A mock client with only 'chat' attribute, no 'responses'
    """
    mock_client = MagicMock(spec_set=['chat'])  # Only has 'chat', not 'responses'
    mock_client.chat = MagicMock()
    return mock_client
