"""
Global Workspace for agent collaboration and peer voting.

Implements Minsky's Society of Mind concepts:
- Agent negotiation through XP voting
- Emergent reputation from peer interactions
- Competition and cooperation dynamics

Reference: Minsky, M. (1986). The Society of Mind. Simon & Schuster.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path


# Vote limits by agent level
VOTE_LIMITS = {
    'worker': {'max_positive': 10, 'max_negative': -5, 'level_range': (1, 9)},
    'team_leader': {'max_positive': 15, 'max_negative': -5, 'level_range': (10, 19)},
    'deputy': {'max_positive': 20, 'max_negative': -10, 'level_range': (20, 29)},
    'supervisor': {'max_positive': 25, 'max_negative': -15, 'level_range': (30, 100)},
}

MAX_VOTES_PER_SESSION = 3


class GlobalWorkspace:
    """
    Global Workspace for multi-agent collaboration.
    
    Manages:
    - Broadcast messages between agents
    - XP voting for peer reputation (Minsky's Society of Mind)
    - Vote history and tracking
    """
    
    def __init__(self, workspace_file: Optional[str] = None):
        """
        Initialize GlobalWorkspace.
        
        Args:
            workspace_file: Optional path to workspace JSON file.
                          If None, uses in-memory storage.
        """
        self.workspace_file = workspace_file
        self.data = {
            'broadcasts': [],
            'xp_votes': [],
            'vote_limits': {},
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        if workspace_file and Path(workspace_file).exists():
            self._load_workspace()
    
    def _load_workspace(self) -> None:
        """Load workspace from file."""
        try:
            with open(self.workspace_file, 'r') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupt or unreadable, start fresh
            print(f"Warning: Could not load workspace file: {e}")
    
    def _save_workspace(self) -> None:
        """Save workspace to file."""
        if self.workspace_file:
            self.data['last_updated'] = datetime.now(timezone.utc).isoformat()
            try:
                with open(self.workspace_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
            except IOError as e:
                print(f"Warning: Could not save workspace file: {e}")
    
    def _get_vote_tier(self, level: int) -> str:
        """
        Get vote tier based on agent level.
        
        Args:
            level: Agent level
            
        Returns:
            Tier name ('worker', 'team_leader', 'deputy', 'supervisor')
        """
        for tier, limits in VOTE_LIMITS.items():
            min_level, max_level = limits['level_range']
            if min_level <= level <= max_level:
                return tier
        return 'supervisor'  # Default to highest tier
    
    def vote_xp(self, voter_alias: str, voter_level: int,
                target_alias: str, xp_delta: int, reason: str) -> Dict[str, Any]:
        """
        Cast an XP vote for another agent.
        
        Implements Minsky's Society of Mind peer negotiation:
        - Agents can endorse (positive vote) or penalize (negative vote)
        - Vote power scales with voter level
        - Limits prevent abuse
        
        Limits (to prevent abuse):
        - Workers (L1-9): Can vote +10 max, -5 max
        - Team Leaders (L10-19): Can vote +15 max, -5 max
        - Deputies (L20-29): Can vote +20 max, -10 max
        - Supervisors (L30+): Can vote +25 max, -15 max
        - Cannot vote for yourself
        - Max 3 votes per agent per session
        
        Args:
            voter_alias: Alias of voting agent (e.g., '@llama')
            voter_level: Level of voting agent
            target_alias: Alias of target agent (e.g., '@claude')
            xp_delta: XP to award (positive) or penalize (negative)
            reason: Justification for the vote
        
        Returns:
            Dict with success status and vote details
        """
        # Normalize aliases (ensure @ prefix)
        if not voter_alias.startswith('@'):
            voter_alias = '@' + voter_alias
        if not target_alias.startswith('@'):
            target_alias = '@' + target_alias
        
        # Validate: Cannot vote for yourself
        if voter_alias == target_alias:
            return {
                'success': False,
                'error': 'Cannot vote for yourself',
                'voter': voter_alias,
                'target': target_alias
            }
        
        # Check vote count limit
        if 'vote_limits' not in self.data:
            self.data['vote_limits'] = {}
        
        if voter_alias not in self.data['vote_limits']:
            self.data['vote_limits'][voter_alias] = {
                'votes_cast': 0,
                'last_reset': datetime.now(timezone.utc).isoformat()
            }
        
        voter_limits = self.data['vote_limits'][voter_alias]
        if voter_limits['votes_cast'] >= MAX_VOTES_PER_SESSION:
            return {
                'success': False,
                'error': f'Vote limit reached ({MAX_VOTES_PER_SESSION} votes per session)',
                'voter': voter_alias,
                'votes_remaining': 0
            }
        
        # Get vote limits based on level
        tier = self._get_vote_tier(voter_level)
        tier_limits = VOTE_LIMITS[tier]
        
        # Validate XP delta is within bounds
        if xp_delta > tier_limits['max_positive']:
            return {
                'success': False,
                'error': f'Vote exceeds positive limit ({tier_limits["max_positive"]} for {tier})',
                'voter': voter_alias,
                'requested': xp_delta,
                'max_allowed': tier_limits['max_positive']
            }
        
        if xp_delta < tier_limits['max_negative']:
            return {
                'success': False,
                'error': f'Vote exceeds negative limit ({tier_limits["max_negative"]} for {tier})',
                'voter': voter_alias,
                'requested': xp_delta,
                'max_allowed': tier_limits['max_negative']
            }
        
        # Create vote record
        vote = {
            'id': f'vote_{uuid.uuid4().hex[:8]}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'voter': voter_alias,
            'voter_level': voter_level,
            'target': target_alias,
            'xp_delta': xp_delta,
            'reason': reason,
            'applied': False
        }
        
        # Add to votes list
        if 'xp_votes' not in self.data:
            self.data['xp_votes'] = []
        self.data['xp_votes'].append(vote)
        
        # Increment vote count
        self.data['vote_limits'][voter_alias]['votes_cast'] += 1
        
        # Save changes
        self._save_workspace()
        
        votes_remaining = MAX_VOTES_PER_SESSION - self.data['vote_limits'][voter_alias]['votes_cast']
        
        return {
            'success': True,
            'vote_id': vote['id'],
            'voter': voter_alias,
            'target': target_alias,
            'xp_delta': xp_delta,
            'votes_remaining': votes_remaining,
            'message': f'{voter_alias} voted {xp_delta:+d} XP for {target_alias}: {reason}'
        }
    
    def get_vote_history(self, agent_alias: Optional[str] = None) -> List[Dict]:
        """
        Get XP vote history, optionally filtered by agent.
        
        Args:
            agent_alias: Optional agent alias to filter by (as voter or target)
        
        Returns:
            List of vote records
        """
        votes = self.data.get('xp_votes', [])
        
        if agent_alias:
            # Normalize alias
            if not agent_alias.startswith('@'):
                agent_alias = '@' + agent_alias
            
            # Filter votes where agent is voter or target
            votes = [
                v for v in votes
                if v['voter'] == agent_alias or v['target'] == agent_alias
            ]
        
        return votes
    
    def get_vote_summary(self) -> Dict[str, int]:
        """
        Get net XP votes per agent.
        
        Returns:
            Dictionary mapping agent alias to net XP from votes
        """
        summary = {}
        
        for vote in self.data.get('xp_votes', []):
            target = vote['target']
            xp_delta = vote['xp_delta']
            
            if target not in summary:
                summary[target] = 0
            summary[target] += xp_delta
        
        return summary
    
    def get_pending_votes(self) -> List[Dict]:
        """
        Get votes that haven't been applied yet.
        
        Returns:
            List of pending vote records
        """
        return [v for v in self.data.get('xp_votes', []) if not v.get('applied', False)]
    
    def mark_vote_applied(self, vote_id: str) -> bool:
        """
        Mark a vote as applied to the database.
        
        Args:
            vote_id: ID of the vote to mark
        
        Returns:
            True if vote was found and marked, False otherwise
        """
        for vote in self.data.get('xp_votes', []):
            if vote['id'] == vote_id:
                vote['applied'] = True
                self._save_workspace()
                return True
        return False
    
    def reset_vote_limits(self) -> None:
        """
        Reset vote limits for all agents.
        
        Call this at the start of a new session.
        """
        self.data['vote_limits'] = {}
        self._save_workspace()
    
    def broadcast(self, category: str, sender: str, message: str, data: Any = None) -> str:
        """
        Broadcast a message to all agents.
        
        Args:
            category: Message category (e.g., 'XP_VOTE', 'STATUS', 'TASK')
            sender: Agent alias sending the broadcast
            message: Human-readable message
            data: Optional structured data
        
        Returns:
            Broadcast ID
        """
        broadcast = {
            'id': f'bc_{uuid.uuid4().hex[:8]}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'category': category,
            'sender': sender,
            'message': message,
            'data': data
        }
        
        if 'broadcasts' not in self.data:
            self.data['broadcasts'] = []
        self.data['broadcasts'].append(broadcast)
        
        self._save_workspace()
        return broadcast['id']
    
    def get_broadcasts(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get recent broadcasts, optionally filtered by category.
        
        Args:
            category: Optional category filter
            limit: Maximum number of broadcasts to return
        
        Returns:
            List of broadcast records (most recent first)
        """
        broadcasts = self.data.get('broadcasts', [])
        
        if category:
            broadcasts = [b for b in broadcasts if b['category'] == category]
        
        # Return most recent first
        return list(reversed(broadcasts[-limit:]))
