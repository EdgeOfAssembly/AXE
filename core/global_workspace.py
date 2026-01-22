"""
Global Workspace for AXE collaborative sessions.
Implements Baars' Global Workspace Theory (1988) for agent coordination.

Theory: Consciousness emerges from a "global broadcast" where specialized
modules post information to a shared workspace, making it available to all.
This enables coordination without central control.

Reference: Baars, B.J. (1988). A Cognitive Theory of Consciousness.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from filelock import FileLock  # For thread-safe file access


class GlobalWorkspace:
    """
    Broadcast mechanism for multi-agent collaborative sessions.
    
    All agents can read the workspace.
    All agents can broadcast findings.
    Higher-level agents (Team Leader+) can broadcast DIRECTIVE entries.
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
        self.workspace_file = self.session_dir / "GLOBAL_WORKSPACE.json"
        self.lock_file = self.session_dir / "GLOBAL_WORKSPACE.lock"
        self._init_workspace()
    
    def _init_workspace(self) -> None:
        """Initialize the workspace file if it doesn't exist."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        if not self.workspace_file.exists():
            initial_data = {
                'version': '1.0',
                'created': datetime.now(timezone.utc).isoformat(),
                'broadcasts': [],
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
        
        # Read, update, write
        data = self._read_workspace()
        data['broadcasts'].append(entry)
        
        # Keep last 200 broadcasts (configurable)
        max_broadcasts = 200
        if len(data['broadcasts']) > max_broadcasts:
            data['broadcasts'] = data['broadcasts'][-max_broadcasts:]
        
        # Update metadata
        data['metadata']['total_broadcasts'] = data['metadata'].get('total_broadcasts', 0) + 1
        if category not in data['metadata'].get('categories_used', []):
            data['metadata'].setdefault('categories_used', []).append(category)
        
        self._write_workspace(data)
        
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
        data = self._read_workspace()
        
        for broadcast in data['broadcasts']:
            if broadcast['id'] == broadcast_id:
                if not broadcast['requires_ack']:
                    return {'success': False, 'reason': 'Broadcast does not require acknowledgment'}
                
                # Check if already acknowledged by this agent
                ack_agents = [a['agent'] for a in broadcast['acks']]
                if agent_alias in ack_agents:
                    return {'success': False, 'reason': 'Already acknowledged'}
                
                # Add acknowledgment
                ack_entry = {
                    'agent': agent_alias,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'comment': comment
                }
                broadcast['acks'].append(ack_entry)
                
                self._write_workspace(data)
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
            broadcasts = [b for b in broadcasts if b['timestamp'] > since]
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
            # Filter to last hour
            cutoff = datetime.now(timezone.utc).isoformat()[:-13]  # Rough hour cutoff
            directives = [d for d in directives if d['timestamp'][:13] >= cutoff[:13]]
        
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
