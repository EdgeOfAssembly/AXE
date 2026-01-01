"""
Token tracking and management system for AXE agents.
Monitors token usage per agent and triggers sleep/spawn when limits are approached.
"""

from typing import Dict, Optional, Tuple
import json

# Token management constants
TOKEN_WARNING_THRESHOLD = 0.80  # Warn at 80% usage
TOKEN_CRITICAL_THRESHOLD = 0.95  # Critical action at 95% usage
TOKEN_REPLACEMENT_ENABLED = True


class TokenTracker:
    """
    Track token usage per agent and manage context limits.
    
    Features:
    - Approximate token counting (chars/4 or tiktoken if available)
    - Threshold warnings at 80% usage
    - Critical action at 95% usage
    - Sleep + summarize + spawn replacement when limits reached
    """
    
    def __init__(self):
        """Initialize the token tracker."""
        self.agent_tokens = {}  # Maps agent_id to token count
        self.agent_limits = {}  # Maps agent_id to max token limit
        
        # Try to import tiktoken for more accurate counting
        self.use_tiktoken = False
        try:
            import tiktoken
            self.tiktoken = tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.use_tiktoken = True
        except ImportError:
            self.tiktoken = None
            self.encoding = None
    
    def set_agent_limit(self, agent_id: str, max_tokens: int) -> None:
        """
        Set the maximum token limit for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            max_tokens: Maximum context window size in tokens
        """
        self.agent_limits[agent_id] = max_tokens
        if agent_id not in self.agent_tokens:
            self.agent_tokens[agent_id] = 0
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken if available, else chars/4.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Approximate number of tokens
        """
        if self.use_tiktoken and self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: approximate as chars/4
            return len(text) // 4
    
    def add_tokens(self, agent_id: str, text: str) -> int:
        """
        Add tokens from text to agent's usage count.
        
        Args:
            agent_id: Unique identifier for the agent
            text: Text that was processed
        
        Returns:
            Updated token count for the agent
        """
        tokens = self.count_tokens(text)
        
        if agent_id not in self.agent_tokens:
            self.agent_tokens[agent_id] = 0
        
        self.agent_tokens[agent_id] += tokens
        return self.agent_tokens[agent_id]
    
    def get_usage(self, agent_id: str) -> Tuple[int, int, float]:
        """
        Get token usage statistics for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Tuple of (tokens_used, max_tokens, usage_percent)
        """
        tokens_used = self.agent_tokens.get(agent_id, 0)
        max_tokens = self.agent_limits.get(agent_id, 0)
        
        if max_tokens > 0:
            usage_percent = tokens_used / max_tokens
        else:
            usage_percent = 0.0
        
        return tokens_used, max_tokens, usage_percent
    
    def check_threshold(self, agent_id: str) -> Tuple[str, Optional[str]]:
        """
        Check if agent has exceeded token thresholds.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Tuple of (status, message) where status is:
            - 'ok': Under 80% usage
            - 'warning': 80-95% usage
            - 'critical': Over 95% usage
        """
        tokens_used, max_tokens, usage_percent = self.get_usage(agent_id)
        
        if usage_percent >= TOKEN_CRITICAL_THRESHOLD:
            remaining = max_tokens - tokens_used
            return 'critical', f"CRITICAL: {usage_percent*100:.1f}% tokens used ({remaining:,} remaining)"
        elif usage_percent >= TOKEN_WARNING_THRESHOLD:
            remaining = max_tokens - tokens_used
            return 'warning', f"WARNING: {usage_percent*100:.1f}% tokens used ({remaining:,} remaining)"
        else:
            return 'ok', None
    
    def reset_agent(self, agent_id: str) -> None:
        """
        Reset token count for an agent (used when creating replacement).
        
        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_tokens[agent_id] = 0
    
    def get_all_usage(self) -> Dict[str, Dict]:
        """
        Get usage statistics for all tracked agents.
        
        Returns:
            Dictionary mapping agent_id to usage stats
        """
        result = {}
        for agent_id in self.agent_tokens.keys():
            tokens_used, max_tokens, usage_percent = self.get_usage(agent_id)
            status, message = self.check_threshold(agent_id)
            
            result[agent_id] = {
                'tokens_used': tokens_used,
                'max_tokens': max_tokens,
                'usage_percent': usage_percent,
                'status': status,
                'message': message
            }
        
        return result
    
    def should_sleep_agent(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if agent should be put to sleep due to token limits.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Tuple of (should_sleep, reason)
        """
        status, message = self.check_threshold(agent_id)
        
        if status == 'critical':
            return True, f"Token limit reached: {message}"
        
        return False, None
    
    def generate_summary_prompt(self, agent_id: str, context: str) -> str:
        """
        Generate a prompt for the agent to summarize its context before sleeping.
        
        Args:
            agent_id: Unique identifier for the agent
            context: Current conversation/work context
        
        Returns:
            Prompt text for summarization
        """
        tokens_used, max_tokens, usage_percent = self.get_usage(agent_id)
        
        prompt = f"""You have reached {usage_percent*100:.1f}% of your token limit ({tokens_used:,}/{max_tokens:,} tokens).

Please create a concise summary of the current conversation and your work so far.
This summary will be given to your replacement agent to continue the work.

Include:
1. Main objectives and goals
2. Key decisions and progress made
3. Current state of the work
4. Open questions or blockers
5. Important context for continuation

Keep the summary under 500 tokens.

Current context to summarize:
{context[:2000]}
"""
        return prompt
    
    def export_stats(self) -> str:
        """
        Export token usage statistics as JSON.
        
        Returns:
            JSON string with all usage statistics
        """
        return json.dumps(self.get_all_usage(), indent=2)
