"""
Context optimization utilities for AXE.
Reduces token usage through intelligent truncation, summarization, and compression.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a conversation message."""
    role: str
    content: str
    tokens: int = 0


class ContextOptimizer:
    """
    Optimizes conversation context to reduce token usage.
    
    Features:
    - Sliding window context management
    - Intelligent message truncation
    - Conversation summarization
    - Duplicate content detection
    """
    
    def __init__(self, token_counter=None):
        """
        Initialize the context optimizer.
        
        Args:
            token_counter: Function to count tokens (defaults to char/4 approximation)
        """
        self.token_counter = token_counter or self._default_token_counter
    
    def _default_token_counter(self, text: str) -> int:
        """Default token counter using char/4 approximation."""
        return len(text) // 4
    
    def optimize_conversation(
        self,
        messages: List[Message],
        max_tokens: int,
        keep_recent: int = 5,
        summarize_old: bool = True
    ) -> List[Message]:
        """
        Optimize a conversation history to fit within token budget.
        
        Strategy:
        1. Keep system message (first)
        2. Keep last N messages (keep_recent)
        3. Summarize older messages if enabled
        4. Truncate if still over budget
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum token budget
            keep_recent: Number of recent messages to always keep
            summarize_old: Whether to summarize old messages
        
        Returns:
            Optimized list of messages within token budget
        """
        if not messages:
            return []
        
        # Calculate current token usage
        total_tokens = sum(m.tokens or self.token_counter(m.content) for m in messages)
        
        if total_tokens <= max_tokens:
            return messages  # Already within budget
        
        # Extract system message (always keep)
        system_msg = messages[0] if messages[0].role == 'system' else None
        conversation = messages[1:] if system_msg else messages
        
        # Keep recent messages
        recent_msgs = conversation[-keep_recent:] if len(conversation) > keep_recent else conversation
        old_msgs = conversation[:-keep_recent] if len(conversation) > keep_recent else []
        
        # Build optimized message list
        optimized = []
        if system_msg:
            optimized.append(system_msg)
        
        # Summarize old messages if enabled and needed
        if old_msgs and summarize_old:
            summary = self._summarize_messages(old_msgs)
            summary_tokens = self.token_counter(summary)
            optimized.append(Message(role='system', content=summary, tokens=summary_tokens))
        
        # Add recent messages
        optimized.extend(recent_msgs)
        
        # Check if we're still over budget
        current_tokens = sum(m.tokens or self.token_counter(m.content) for m in optimized)
        
        if current_tokens > max_tokens:
            # More aggressive truncation needed
            optimized = self._truncate_to_budget(optimized, max_tokens)
        
        return optimized
    
    def _summarize_messages(self, messages: List[Message]) -> str:
        """
        Create a summary of older messages.
        
        Args:
            messages: Messages to summarize
        
        Returns:
            Summary text
        """
        # Extract key points from messages
        key_content = []
        
        for msg in messages:
            # Remove READ blocks and verbose output
            cleaned = self._clean_message_content(msg.content)
            
            # Extract commands and important statements
            if '```' in cleaned or '[EXEC]' in cleaned or '@' in cleaned[:20]:
                key_content.append(f"{msg.role}: {cleaned[:200]}")
        
        if not key_content:
            return f"[Conversation summary: {len(messages)} earlier messages omitted for token optimization]"
        
        summary = "[Summary of earlier conversation]\n" + "\n".join(key_content[:10])
        return summary[:500]  # Cap summary length
    
    def _clean_message_content(self, content: str) -> str:
        """
        Remove verbose or redundant content from messages.
        
        Args:
            content: Original message content
        
        Returns:
            Cleaned content
        """
        # Remove READ blocks
        content = re.sub(r'\[READ[^\]]*\].*?(?=\n\n|\n\[(?!\[)[A-Z]|\Z)', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Remove very long code blocks (keep first 50 lines)
        content = self._truncate_code_blocks(content, max_lines=50)
        
        return content.strip()
    
    def _truncate_code_blocks(self, content: str, max_lines: int = 50) -> str:
        """
        Truncate long code blocks to save tokens.
        
        Args:
            content: Content with code blocks
            max_lines: Maximum lines per code block
        
        Returns:
            Content with truncated code blocks
        """
        def truncate_block(match):
            block = match.group(0)
            lines = block.split('\n')
            
            if len(lines) <= max_lines + 2:  # +2 for fence markers
                return block
            
            lang = match.group(1) or ''
            truncated = '\n'.join(lines[:max_lines])
            remaining = len(lines) - max_lines
            return f"```{lang}\n{truncated}\n... ({remaining} more lines omitted for token optimization)\n```"
        
        # Match code blocks
        pattern = r'```(\w*)\n(.*?)```'
        return re.sub(pattern, truncate_block, content, flags=re.DOTALL)
    
    def _truncate_to_budget(self, messages: List[Message], max_tokens: int) -> List[Message]:
        """
        Aggressively truncate messages to fit budget.
        
        Args:
            messages: Messages to truncate
            max_tokens: Maximum token budget
        
        Returns:
            Truncated messages within budget
        """
        # Keep system message and as many recent messages as possible
        if not messages:
            return []
        
        result = []
        token_count = 0
        
        # Add messages from the end (most recent first)
        for msg in reversed(messages):
            msg_tokens = msg.tokens or self.token_counter(msg.content)
            
            if token_count + msg_tokens <= max_tokens:
                result.insert(0, msg)
                token_count += msg_tokens
            elif msg.role == 'system':
                # Try to keep system message by truncating it
                available = max_tokens - token_count
                if available > 100:  # Need at least 100 tokens
                    truncated_content = msg.content[:available * 4]  # Rough conversion
                    truncated_msg = Message(
                        role=msg.role,
                        content=truncated_content + "\n...(truncated for token optimization)",
                        tokens=available
                    )
                    result.insert(0, truncated_msg)
                break
        
        return result
    
    def compress_prompt(self, prompt: str) -> str:
        """
        Compress a prompt by removing redundancy and verbosity.
        
        Args:
            prompt: Original prompt
        
        Returns:
            Compressed prompt
        """
        # Remove excessive examples
        compressed = self._reduce_examples(prompt)
        
        # Remove redundant phrases
        compressed = self._remove_redundancy(compressed)
        
        # Clean whitespace
        compressed = re.sub(r'\n{3,}', '\n\n', compressed)
        compressed = re.sub(r' {2,}', ' ', compressed)
        
        return compressed.strip()
    
    def _reduce_examples(self, text: str) -> str:
        """
        Reduce number of examples in text.
        
        Args:
            text: Text with examples
        
        Returns:
            Text with fewer examples
        """
        # Find example sections
        examples_pattern = r'(Examples?:|For example:)(.*?)(?=\n\n[A-Z]|\n#|\Z)'
        
        def shorten_examples(match):
            header = match.group(1)
            examples_text = match.group(2)
            
            # Keep only first 2-3 examples
            examples = re.split(r'\n\s*[-*•]\s+', examples_text)
            kept = examples[:3] if len(examples) > 3 else examples
            
            return header + '\n- ' + '\n- '.join(kept) + '\n'
        
        return re.sub(examples_pattern, shorten_examples, text, flags=re.DOTALL | re.IGNORECASE)
    
    def _remove_redundancy(self, text: str) -> str:
        """
        Remove redundant phrases and repetition.
        
        Args:
            text: Text to process
        
        Returns:
            Text with reduced redundancy
        """
        # Common redundant phrases in prompts
        redundant_phrases = [
            r'(?:Please |Kindly )*(?:make sure|ensure) (?:to |that you )',
            r'(?:You should|You must|You need to) always ',
            r'It is important (?:to note )?that ',
            r'Please note that ',
            r'As mentioned (?:earlier|above|previously), ',
        ]
        
        result = text
        for pattern in redundant_phrases:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        return result
    
    def deduplicate_context(self, messages: List[Message]) -> List[Message]:
        """
        Remove duplicate or near-duplicate messages.
        
        Args:
            messages: List of messages
        
        Returns:
            Deduplicated messages
        """
        seen_content = set()
        deduplicated = []
        
        for msg in messages:
            # Create a fingerprint of the message
            fingerprint = self._create_fingerprint(msg.content)
            
            if fingerprint not in seen_content:
                seen_content.add(fingerprint)
                deduplicated.append(msg)
        
        return deduplicated
    
    def _create_fingerprint(self, content: str) -> str:
        """
        Create a fingerprint for content deduplication.
        
        Args:
            content: Message content
        
        Returns:
            Fingerprint string
        """
        # Normalize and hash content
        normalized = content.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Use first 200 chars as fingerprint
        return normalized[:200]


def create_sliding_window(
    messages: List[Dict],
    window_size: int,
    overlap: int = 0
) -> List[List[Dict]]:
    """
    Create sliding windows over messages for processing in chunks.
    
    Args:
        messages: List of messages
        window_size: Size of each window
        overlap: Number of messages to overlap between windows
    
    Returns:
        List of message windows
    """
    if not messages or window_size <= 0:
        return []
    
    windows = []
    step = window_size - overlap
    
    for i in range(0, len(messages), step):
        window = messages[i:i + window_size]
        if window:  # Don't add empty windows
            windows.append(window)
    
    return windows


def estimate_token_savings(original_tokens: int, optimized_tokens: int) -> Dict[str, any]:
    """
    Calculate token savings statistics.
    
    Args:
        original_tokens: Original token count
        optimized_tokens: Optimized token count
    
    Returns:
        Dictionary with savings statistics
    """
    if original_tokens == 0:
        return {
            'savings': 0,
            'percent': 0.0,
            'original': 0,
            'optimized': 0
        }
    
    savings = original_tokens - optimized_tokens
    percent = (savings / original_tokens) * 100
    
    return {
        'savings': savings,
        'percent': percent,
        'original': original_tokens,
        'optimized': optimized_tokens
    }
