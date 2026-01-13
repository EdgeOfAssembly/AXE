"""
Anthropic-specific features for AXE.

This module provides centralized functionality for Anthropic Claude-specific features:
- Prompt caching
- Files API
- Extended thinking
- Token counting

All features maintain backward compatibility with other providers.
"""

import os
from typing import Optional, List, Dict, Any, Tuple
from utils.formatting import Colors, c

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class AnthropicFeatures:
    """Manager for Anthropic-specific features."""
    
    def __init__(self, client: Any = None, config: Dict[str, Any] = None):
        """
        Initialize Anthropic features manager.
        
        Args:
            client: Anthropic API client instance
            config: Configuration dictionary from models.yaml
        """
        self.client = client
        self.config = config or {}
        
        # Parse feature configurations
        self.prompt_caching = self.config.get('prompt_caching', {})
        self.files_api = self.config.get('files_api', {})
        self.token_counting = self.config.get('token_counting', {})
    
    def is_prompt_caching_enabled(self) -> bool:
        """Check if prompt caching is enabled."""
        return self.prompt_caching.get('enabled', True)  # Default to True for Anthropic
    
    def is_files_api_enabled(self) -> bool:
        """Check if Files API is enabled."""
        return self.files_api.get('enabled', False)  # Default to False (beta)
    
    def is_token_counting_enabled(self) -> bool:
        """Check if token counting is enabled."""
        return self.token_counting.get('enabled', True)
    
    def get_cache_breakpoints(self) -> List[str]:
        """Get configured cache breakpoints."""
        return self.prompt_caching.get('cache_breakpoints', ['system', 'tools'])
    
    def get_cache_ttl(self) -> str:
        """Get cache TTL setting."""
        return self.prompt_caching.get('default_ttl', '5m')
    
    def add_cache_control(self, content_blocks: List[Dict], breakpoints: List[str] = None) -> List[Dict]:
        """
        Add cache_control markers to content blocks based on breakpoints.
        
        Args:
            content_blocks: List of content blocks to mark for caching
            breakpoints: Optional list of breakpoint names (defaults to config)
        
        Returns:
            List of content blocks with cache_control added where appropriate
        """
        if not self.is_prompt_caching_enabled():
            return content_blocks
        
        if not content_blocks:
            return content_blocks
        
        # Add cache_control to the last block (this caches everything up to this point)
        # This is the standard Anthropic pattern for prompt caching
        result = content_blocks.copy()
        if result:
            last_block = result[-1].copy()
            last_block['cache_control'] = {'type': 'ephemeral'}
            result[-1] = last_block
        
        return result
    
    def count_tokens(self, model: str, messages: List[Dict], system: str = "", 
                     tools: List[Dict] = None) -> Optional[int]:
        """
        Get precise token count from Anthropic API.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            system: System prompt string
            tools: Optional list of tool definitions
        
        Returns:
            Token count, or None if error/disabled
        """
        if not self.is_token_counting_enabled() or not self.client:
            return None
        
        try:
            # Build request parameters
            params = {
                'model': model,
                'messages': messages
            }
            
            if system:
                params['system'] = system
            
            if tools:
                params['tools'] = tools
            
            # Call token counting endpoint
            response = self.client.messages.count_tokens(**params)
            return response.input_tokens
        
        except Exception as e:
            print(c(f"Token counting failed: {e}", Colors.YELLOW))
            return None
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using char/4 heuristic.
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def should_use_precise_counting(self, estimated_tokens: int) -> bool:
        """
        Check if precise token counting should be used based on threshold.
        
        Args:
            estimated_tokens: Estimated token count
        
        Returns:
            True if precise counting should be used
        """
        threshold = self.token_counting.get('threshold_estimated_tokens', 10000)
        return self.is_token_counting_enabled() and estimated_tokens > threshold


class FilesAPIManager:
    """Manager for Anthropic Files API operations."""
    
    def __init__(self, client: Any = None, config: Dict[str, Any] = None):
        """
        Initialize Files API manager.
        
        Args:
            client: Anthropic API client instance
            config: Configuration dictionary
        """
        self.client = client
        self.config = config or {}
        self.beta_header = 'files-api-2025-04-14'
    
    def is_enabled(self) -> bool:
        """Check if Files API is enabled."""
        return self.config.get('enabled', False)
    
    def get_upload_threshold_kb(self) -> int:
        """Get file upload threshold in KB."""
        return self.config.get('upload_threshold_kb', 50)
    
    def should_upload_file(self, file_size_bytes: int) -> bool:
        """
        Check if a file should be uploaded based on size threshold.
        
        Args:
            file_size_bytes: File size in bytes
        
        Returns:
            True if file should be uploaded
        """
        threshold_bytes = self.get_upload_threshold_kb() * 1024
        return self.is_enabled() and file_size_bytes > threshold_bytes
    
    def upload_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Anthropic.
        
        Args:
            file_path: Path to file to upload
        
        Returns:
            File metadata dict with 'id', 'filename', etc., or None if failed
        """
        if not self.is_enabled() or not self.client:
            return None
        
        try:
            # Note: This is a placeholder - actual implementation would use
            # the Anthropic SDK's files API once it's available
            print(c(f"Note: Files API upload not yet implemented in SDK", Colors.YELLOW))
            return None
        
        except Exception as e:
            print(c(f"File upload failed: {e}", Colors.YELLOW))
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Anthropic.
        
        Args:
            file_id: File ID to delete
        
        Returns:
            True if successful
        """
        if not self.is_enabled() or not self.client:
            return False
        
        try:
            # Note: Placeholder for actual implementation
            print(c(f"Note: Files API delete not yet implemented in SDK", Colors.YELLOW))
            return False
        
        except Exception as e:
            print(c(f"File delete failed: {e}", Colors.YELLOW))
            return False
    
    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all uploaded files.
        
        Returns:
            List of file metadata dicts
        """
        if not self.is_enabled() or not self.client:
            return []
        
        try:
            # Note: Placeholder for actual implementation
            return []
        
        except Exception as e:
            print(c(f"File list failed: {e}", Colors.YELLOW))
            return []


def get_anthropic_features(client: Any, config: Dict[str, Any]) -> AnthropicFeatures:
    """
    Factory function to create AnthropicFeatures instance.
    
    Args:
        client: Anthropic API client
        config: Configuration from models.yaml
    
    Returns:
        AnthropicFeatures instance
    """
    return AnthropicFeatures(client=client, config=config)


def get_files_api_manager(client: Any, config: Dict[str, Any]) -> FilesAPIManager:
    """
    Factory function to create FilesAPIManager instance.
    
    Args:
        client: Anthropic API client
        config: Configuration from models.yaml
    
    Returns:
        FilesAPIManager instance
    """
    return FilesAPIManager(client=client, config=config)
