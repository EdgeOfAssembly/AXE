"""
Global Workspace for AXE collaborative sessions.
Implements Baars' Global Workspace Theory (1988) for agent coordination
and Minsky's Society of Mind (1986) peer voting for reputation.

Theory: Consciousness emerges from a "global broadcast" where specialized
modules post information to a shared workspace, making it available to all.
This enables coordination without central control. Peer voting allows
agents to negotiate and build reputation through interactions.

References:
- Baars, B.J. (1988). A Cognitive Theory of Consciousness.
- Minsky, M. (1986). The Society of Mind. Simon & Schuster.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from filelock import FileLock  # For thread-safe file access

from .constants import GLOBAL_WORKSPACE_MAX_BROADCASTS, GLOBAL_WORKSPACE_FILE


# Vote limits by agent level (Minsky's Society of Mind - peer negotiation)
VOTE_LIMITS = {
    'worker': {'max_positive': 10, 'max_negative': -5, 'level_range': (1, 9)},
    'team_leader': {'max_positive': 15, 'max_negative': -5, 'level_range': (10, 19)},
    'deputy': {'max_positive': 20, 'max_negative': -10, 'level_range': (20, 29)},
    'supervisor': {'max_positive': 25, 'max_negative': -15, 'level_range': (30, 100)},
}

MAX_VOTES_PER_SESSION = 3


class GlobalWorkspace:
    """
    Broadcast mechanism for multi-agent collaborative sessions.
    
    All agents can read the workspace.
    All agents can broadcast findings.
    Higher-level agents (Team Leader+) can broadcast DIRECTIVE entries.
    Agents can vote XP for peers (Minsky's Society of Mind peer negotiation).
    """
    
    # Broadcast categories aligned with AXE's focus areas
    CATEGORIES = [
        'SECURITY',      # Security findings (vulnerabilities, risks)
        'BUG',           # Bug discoveries
        'OPTIMIZATION',  # Performance/code improvements
        'CONFLICT',      # Conflicting findings requiring resolution
        'DIRECTIVE',     # High-level directives (Team Leader+ only)
        'STATUS',        # Status updates
        'XP_VOTE',       # Peer XP voting
        'FINDING',       # General findings
    ]
    
    # Minimum level required for DIRECTIVE broadcasts
    DIRECTIVE_MIN_LEVEL = 20  # Team Leader
    
    def __init__(self, session_dir: str):
        """
        Initialize the Global Workspace for a session.
        
        Args:
            session_dir: Directory for the collaborative session
        """
        self.session_dir = Path(session_dir)
        self.workspace_file = self.session_dir / GLOBAL_WORKSPACE_FILE
        self.lock_file = self.session_dir / f"{GLOBAL_WORKSPACE_FILE}.lock"
        self._init_workspace()
    
    def _init_workspace(self) -> None:
        """Initialize the workspace file if it doesn't exist."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        if not self.workspace_file.exists():
            initial_data = {
                'version': '1.0',
                'created': datetime.now(timezone.utc).isoformat(),
                'broadcasts': [],
                'xp_votes': [],
                'vote_limits': {},
                'metadata': {
                    'total_broadcasts': 0,
                    'categories_used': []
                }
            }
            self._write_workspace(initial_data)
    
    def _read_workspace(self) -> Dict[str, Any]:
        """Thread-safe read of workspace file."""
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                return json.loads(self.workspace_file.read_text())
            return {'broadcasts': [], 'metadata': {}}
    
    def _write_workspace(self, data: Dict[str, Any]) -> None:
        """Thread-safe write to workspace file."""
        with FileLock(str(self.lock_file)):
            self.workspace_file.write_text(json.dumps(data, indent=2))
    
    def broadcast(self, agent_alias: str, agent_level: int,
                  category: str, message: str,
                  requires_ack: bool = False,
                  related_file: Optional[str] = None,
                  tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post a broadcast to the global workspace.
        
        Args:
            agent_alias: The broadcasting agent's alias (e.g., @llama1)
            agent_level: The agent's current level (1-40+)
            category: Broadcast category (from CATEGORIES)
            message: The broadcast message
            requires_ack: Whether other agents must acknowledge this
            related_file: Optional file path related to this broadcast
            tags: Optional tags for filtering
        
        Returns:
            Dict with success status and broadcast_id or error reason
        """
        # Validate category
        if category not in self.CATEGORIES:
            return {'success': False, 'reason': f'Invalid category: {category}'}
        
        # Check permission for DIRECTIVE
        if category == 'DIRECTIVE' and agent_level < self.DIRECTIVE_MIN_LEVEL:
            return {
                'success': False, 
                'reason': f'DIRECTIVE requires level {self.DIRECTIVE_MIN_LEVEL}+ (Team Leader)'
            }
        
        # Generate unique broadcast ID
        timestamp = datetime.now(timezone.utc)
        broadcast_id = f"{timestamp.strftime('%Y%m%d%H%M%S%f')}_{agent_alias.replace('@', '')}"
        
        entry = {
            'id': broadcast_id,
            'timestamp': timestamp.isoformat(),
            'agent': agent_alias,
            'level': agent_level,
            'category': category,
            'message': message,
            'requires_ack': requires_ack,
            'acks': [],
            'related_file': related_file,
            'tags': tags or []
        }
        
        # Perform the full read-modify-write under a single file lock for thread safety
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                data = json.loads(self.workspace_file.read_text())
            else:
                data = {'broadcasts': [], 'metadata': {}}
            
            data['broadcasts'].append(entry)
            
            # Keep last N broadcasts (from constants)
            if len(data['broadcasts']) > GLOBAL_WORKSPACE_MAX_BROADCASTS:
                data['broadcasts'] = data['broadcasts'][-GLOBAL_WORKSPACE_MAX_BROADCASTS:]
            
            # Update metadata
            data['metadata']['total_broadcasts'] = data['metadata'].get('total_broadcasts', 0) + 1
            if category not in data['metadata'].get('categories_used', []):
                data['metadata'].setdefault('categories_used', []).append(category)
            
            self.workspace_file.write_text(json.dumps(data, indent=2))
        
        return {'success': True, 'broadcast_id': broadcast_id, 'entry': entry}
    
    def acknowledge(self, broadcast_id: str, agent_alias: str, 
                    comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Acknowledge a broadcast that requires acknowledgment.
        
        Args:
            broadcast_id: ID of the broadcast to acknowledge
            agent_alias: Alias of the acknowledging agent
            comment: Optional comment with the acknowledgment
        
        Returns:
            Dict with success status
        """
        # Perform the full read-modify-write under a single file lock for thread safety
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                data = json.loads(self.workspace_file.read_text())
            else:
                data = {'broadcasts': [], 'metadata': {}}
            
            for broadcast in data.get('broadcasts', []):
                if broadcast.get('id') == broadcast_id:
                    if not broadcast.get('requires_ack'):
                        return {
                            'success': False,
                            'reason': 'Broadcast does not require acknowledgment'
                        }
                    
                    # Check if already acknowledged by this agent
                    ack_agents = [a.get('agent') for a in broadcast.get('acks', [])]
                    if agent_alias in ack_agents:
                        return {'success': False, 'reason': 'Already acknowledged'}
                    
                    # Add acknowledgment
                    ack_entry = {
                        'agent': agent_alias,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'comment': comment
                    }
                    broadcast.setdefault('acks', []).append(ack_entry)
                    
                    self.workspace_file.write_text(json.dumps(data, indent=2))
                    return {'success': True, 'broadcast_id': broadcast_id}
            
            return {'success': False, 'reason': 'Broadcast not found'}
    
    def get_broadcasts(self, 
                       since: Optional[str] = None,
                       category: Optional[str] = None,
                       agent: Optional[str] = None,
                       requires_ack_only: bool = False,
                       limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get broadcasts with optional filtering.
        
        Args:
            since: ISO timestamp - only return broadcasts after this time
            category: Filter by category
            agent: Filter by agent alias
            requires_ack_only: Only return broadcasts requiring acknowledgment
            limit: Maximum number of broadcasts to return
        
        Returns:
            List of broadcast entries (newest first)
        """
        data = self._read_workspace()
        broadcasts = data.get('broadcasts', [])
        
        # Apply filters
        if since:
            # Parse the provided 'since' timestamp as an aware datetime
            try:
                since_str = since
                if since_str.endswith("Z"):
                    since_str = since_str.replace("Z", "+00:00")
                since_dt = datetime.fromisoformat(since_str)
            except (TypeError, ValueError):
                # If 'since' is not a valid ISO-8601 timestamp, skip time-based filtering
                since_dt = None
            
            if since_dt is not None:
                filtered_broadcasts: List[Dict[str, Any]] = []
                for b in broadcasts:
                    ts_str = b.get("timestamp")
                    if not ts_str:
                        continue
                    try:
                        ts_norm = ts_str
                        if isinstance(ts_norm, str) and ts_norm.endswith("Z"):
                            ts_norm = ts_norm.replace("Z", "+00:00")
                        ts_dt = datetime.fromisoformat(ts_norm)
                    except (TypeError, ValueError):
                        # Skip broadcasts with unparsable timestamps for the 'since' filter
                        continue
                    if ts_dt > since_dt:
                        filtered_broadcasts.append(b)
                broadcasts = filtered_broadcasts
        
        if category:
            broadcasts = [b for b in broadcasts if b['category'] == category]
        if agent:
            broadcasts = [b for b in broadcasts if b['agent'] == agent]
        if requires_ack_only:
            broadcasts = [b for b in broadcasts if b['requires_ack']]
        
        # Return newest first, limited
        return list(reversed(broadcasts))[:limit]
    
    def get_pending_acks(self, agent_alias: str) -> List[Dict[str, Any]]:
        """
        Get broadcasts requiring acknowledgment from this agent.
        
        Args:
            agent_alias: The agent to check for pending acks
        
        Returns:
            List of broadcasts needing ack from this agent
        """
        data = self._read_workspace()
        pending = []
        
        for broadcast in data['broadcasts']:
            if broadcast['requires_ack']:
                ack_agents = [a['agent'] for a in broadcast['acks']]
                # Don't require self-ack
                if agent_alias not in ack_agents and broadcast['agent'] != agent_alias:
                    pending.append(broadcast)
        
        return pending
    
    def get_conflicts(self) -> List[Dict[str, Any]]:
        """
        Get all unresolved CONFLICT broadcasts.
        
        Returns:
            List of CONFLICT broadcasts that haven't been resolved
        """
        return self.get_broadcasts(category='CONFLICT', requires_ack_only=True)
    
    def get_directives(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get DIRECTIVE broadcasts from leadership.
        
        Args:
            active_only: Only return recent directives (last hour)
        
        Returns:
            List of DIRECTIVE broadcasts
        """
        directives = self.get_broadcasts(category='DIRECTIVE')
        
        if active_only:
            # Filter to last hour using proper datetime arithmetic
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            filtered_directives: List[Dict[str, Any]] = []
            for d in directives:
                ts_str = d.get('timestamp')
                if not ts_str:
                    continue
                try:
                    ts_norm = ts_str
                    if isinstance(ts_norm, str) and ts_norm.endswith("Z"):
                        ts_norm = ts_norm.replace("Z", "+00:00")
                    ts_dt = datetime.fromisoformat(ts_norm)
                    if ts_dt >= cutoff_time:
                        filtered_directives.append(d)
                except (TypeError, ValueError):
                    # Skip directives with unparsable timestamps
                    continue
            directives = filtered_directives
        
        return directives
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the workspace state.
        
        Returns:
            Summary dict with counts and recent activity
        """
        data = self._read_workspace()
        broadcasts = data.get('broadcasts', [])
        
        # Count by category
        category_counts = {}
        for b in broadcasts:
            cat = b['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Count pending acks
        pending_acks = sum(1 for b in broadcasts 
                         if b['requires_ack'] and len(b['acks']) == 0)
        
        return {
            'total_broadcasts': len(broadcasts),
            'by_category': category_counts,
            'pending_acks': pending_acks,
            'metadata': data.get('metadata', {})
        }
    
    def format_for_prompt(self, agent_alias: str, max_entries: int = 10) -> str:
        """
        Format recent broadcasts for inclusion in agent prompts.
        
        Args:
            agent_alias: The agent receiving the prompt
            max_entries: Maximum entries to include
        
        Returns:
            Formatted string for prompt injection
        """
        recent = self.get_broadcasts(limit=max_entries)
        pending = self.get_pending_acks(agent_alias)
        
        lines = ["## GLOBAL WORKSPACE (Recent Broadcasts)"]
        
        if pending:
            lines.append(f"\n⚠️ **{len(pending)} broadcasts require your acknowledgment**\n")
        
        for b in recent:
            ack_status = ""
            if b['requires_ack']:
                ack_count = len(b['acks'])
                ack_status = f" [ACK: {ack_count}]"
            
            lines.append(
                f"- [{b['category']}] {b['agent']} (L{b['level']}): "
                f"{b['message'][:100]}{'...' if len(b['message']) > 100 else ''}{ack_status}"
            )
        
        if not recent:
            lines.append("(No recent broadcasts)")
        
        return "\n".join(lines)
    
    # ============================================================================
    # XP Voting System (Minsky's Society of Mind - Peer Negotiation)
    # ============================================================================
    
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
        
        # Perform the full read-modify-write under a single file lock
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                data = json.loads(self.workspace_file.read_text())
            else:
                data = {'broadcasts': [], 'xp_votes': [], 'vote_limits': {}, 'metadata': {}}
            
            # Check vote count limit
            if 'vote_limits' not in data:
                data['vote_limits'] = {}
            
            if voter_alias not in data['vote_limits']:
                data['vote_limits'][voter_alias] = {
                    'votes_cast': 0,
                    'last_reset': datetime.now(timezone.utc).isoformat()
                }
            
            voter_limits = data['vote_limits'][voter_alias]
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
            if 'xp_votes' not in data:
                data['xp_votes'] = []
            data['xp_votes'].append(vote)
            
            # Increment vote count
            data['vote_limits'][voter_alias]['votes_cast'] += 1
            
            # Save changes
            self.workspace_file.write_text(json.dumps(data, indent=2))
            
            votes_remaining = MAX_VOTES_PER_SESSION - data['vote_limits'][voter_alias]['votes_cast']
            
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
        data = self._read_workspace()
        votes = data.get('xp_votes', [])
        
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
        data = self._read_workspace()
        summary = {}
        
        for vote in data.get('xp_votes', []):
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
        data = self._read_workspace()
        return [v for v in data.get('xp_votes', []) if not v.get('applied', False)]
    
    def mark_vote_applied(self, vote_id: str) -> bool:
        """
        Mark a vote as applied to the database.
        
        Args:
            vote_id: ID of the vote to mark
        
        Returns:
            True if vote was found and marked, False otherwise
        """
        # Perform the full read-modify-write under a single file lock
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                data = json.loads(self.workspace_file.read_text())
            else:
                return False
            
            for vote in data.get('xp_votes', []):
                if vote['id'] == vote_id:
                    vote['applied'] = True
                    self.workspace_file.write_text(json.dumps(data, indent=2))
                    return True
            return False
    
    def reset_vote_limits(self) -> None:
        """
        Reset vote limits for all agents.
        
        Call this at the start of a new session.
        """
        # Perform the full read-modify-write under a single file lock
        with FileLock(str(self.lock_file)):
            if self.workspace_file.exists():
                data = json.loads(self.workspace_file.read_text())
            else:
                data = {'broadcasts': [], 'xp_votes': [], 'vote_limits': {}, 'metadata': {}}
            
            data['vote_limits'] = {}
            self.workspace_file.write_text(json.dumps(data, indent=2))
