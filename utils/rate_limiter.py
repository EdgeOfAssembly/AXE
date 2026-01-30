"""
Rate limiting for API calls to prevent quota burnout.
Implements sliding window token tracking.
"""
import time
from collections import deque
from typing import Dict, Optional, Tuple
class RateLimiter:
    """
    Rate limiter with sliding window token tracking.
    Prevents API quota burnout by limiting tokens per minute per agent.
    """
    def __init__(self, config: Dict):
        """
        Initialize rate limiter with configuration.
        Args:
            config: Dictionary with rate limit configuration:
                - enabled: Whether rate limiting is enabled
                - tokens_per_minute: Global token limit per minute
                - per_agent: Dict of per-agent limits
        """
        self.enabled = config.get('enabled', False)
        self.global_limit = config.get('tokens_per_minute', 10000)
        self.per_agent_limits = config.get('per_agent', {})
        # Track token usage per agent with timestamps
        # Format: {agent_name: deque([(timestamp, token_count), ...])}
        self.usage_history: Dict[str, deque] = {}
    def check_limit(self, agent_name: str, tokens_to_add: int) -> Tuple[bool, Optional[str]]:
        """
        Check if adding tokens would exceed rate limit.
        Args:
            agent_name: Name of the agent
            tokens_to_add: Number of tokens to add
        Returns:
            Tuple of (allowed: bool, message: Optional[str])
            - If allowed, message is None
            - If not allowed, message explains why and when limit resets
        """
        if not self.enabled:
            return True, None
        # Get agent-specific limit or use global limit
        agent_limit = self.per_agent_limits.get(agent_name, self.global_limit)
        # Special case: "unlimited" string means no limit
        if isinstance(agent_limit, str) and agent_limit.lower() == "unlimited":
            return True, None
        # Initialize history for new agents
        if agent_name not in self.usage_history:
            self.usage_history[agent_name] = deque()
        # Remove entries older than 1 minute
        current_time = time.time()
        one_minute_ago = current_time - 60
        history = self.usage_history[agent_name]
        while history and history[0][0] < one_minute_ago:
            history.popleft()
        # Calculate current usage in the last minute
        current_usage = sum(count for _, count in history)
        # Check if adding tokens would exceed limit
        if current_usage + tokens_to_add > agent_limit:
            # Calculate when limit will reset
            if history:
                oldest_timestamp = history[0][0]
                reset_in = int(60 - (current_time - oldest_timestamp))
                message = (
                    f"Rate limit exceeded for {agent_name}. "
                    f"Used {current_usage:,} of {agent_limit:,} tokens/min. "
                    f"Limit resets in {reset_in}s."
                )
            else:
                message = f"Rate limit exceeded for {agent_name}."
            return False, message
        return True, None
    def add_tokens(self, agent_name: str, token_count: int) -> None:
        """
        Record token usage for an agent.
        Args:
            agent_name: Name of the agent
            token_count: Number of tokens used
        """
        if not self.enabled:
            return
        if agent_name not in self.usage_history:
            self.usage_history[agent_name] = deque()
        current_time = time.time()
        self.usage_history[agent_name].append((current_time, token_count))
    def get_current_usage(self, agent_name: str) -> Tuple[int, int]:
        """
        Get current token usage for an agent in the last minute.
        Args:
            agent_name: Name of the agent
        Returns:
            Tuple of (current_usage, limit)
        """
        if agent_name not in self.usage_history:
            agent_limit = self.per_agent_limits.get(agent_name, self.global_limit)
            if isinstance(agent_limit, str) and agent_limit.lower() == "unlimited":
                return 0, 0  # Special case for unlimited
            return 0, agent_limit
        # Remove entries older than 1 minute
        current_time = time.time()
        one_minute_ago = current_time - 60
        history = self.usage_history[agent_name]
        while history and history[0][0] < one_minute_ago:
            history.popleft()
        # Calculate current usage
        current_usage = sum(count for _, count in history)
        agent_limit = self.per_agent_limits.get(agent_name, self.global_limit)
        if isinstance(agent_limit, str) and agent_limit.lower() == "unlimited":
            return current_usage, 0  # Special case for unlimited
        return current_usage, agent_limit
    def get_all_usage(self) -> Dict[str, Tuple[int, int]]:
        """
        Get current usage for all tracked agents.
        Returns:
            Dictionary mapping agent_name to (current_usage, limit)
        """
        result = {}
        for agent_name in self.usage_history.keys():
            result[agent_name] = self.get_current_usage(agent_name)
        return result