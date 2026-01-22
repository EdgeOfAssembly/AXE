"""
Global Workspace for AXE multiagent system.

Implements broadcast-based communication inspired by Bernard Baars' Global Workspace Theory
and Marvin Minsky's Society of Mind concepts. Agents broadcast findings to a shared workspace
where conflicts can be detected and arbitrated.

Reference:
- Baars, B. J. (1988). A Cognitive Theory of Consciousness.
- Minsky, M. (1986). The Society of Mind. Chapters 17-19.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple


class GlobalWorkspace:
    """
    Shared workspace for agent broadcasts and conflict detection.
    
    Provides:
    - Broadcast history tracking
    - Conflict detection via keyword analysis
    - Manual conflict flagging
    - Integration with arbitration protocol
    """
    
    def __init__(self, db=None):
        """
        Initialize the global workspace.
        
        Args:
            db: Optional AgentDatabase instance for persistence
        """
        self.db = db
        self.broadcasts: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []
        
    def broadcast(self, agent_alias: str, agent_level: int, 
                  category: str, content: str, 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a broadcast to the global workspace.
        
        Args:
            agent_alias: Alias of broadcasting agent
            agent_level: Level of broadcasting agent
            category: Category of broadcast (e.g., 'SECURITY', 'CODE_QUALITY', 'CONFLICT')
            content: Broadcast content/message
            metadata: Optional metadata (affected files, functions, etc.)
            
        Returns:
            Broadcast ID (UUID)
        """
        broadcast_id = str(uuid.uuid4())
        broadcast = {
            'id': broadcast_id,
            'agent_alias': agent_alias,
            'agent_level': agent_level,
            'category': category,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        self.broadcasts.append(broadcast)
        
        # Persist to database if available
        if self.db:
            self._persist_broadcast(broadcast)
            
        return broadcast_id
    
    def get_broadcasts(self, limit: Optional[int] = None, 
                      category: Optional[str] = None,
                      agent_alias: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve broadcasts from the workspace.
        
        Args:
            limit: Maximum number of broadcasts to return (most recent first)
            category: Filter by category
            agent_alias: Filter by agent
            
        Returns:
            List of broadcasts
        """
        filtered = self.broadcasts
        
        if category:
            filtered = [b for b in filtered if b['category'] == category]
        
        if agent_alias:
            filtered = [b for b in filtered if b['agent_alias'] == agent_alias]
            
        if limit:
            filtered = filtered[-limit:]
            
        return filtered
    
    def detect_conflicts(self, window_broadcasts: int = 20) -> List[Dict[str, Any]]:
        """
        Detect conflicting broadcasts in recent history.
        
        Conflict signals:
        - Same category, different agents, contradictory keywords
        - Explicit CONFLICT category broadcasts
        - Opposing recommendations on same file/function
        
        Args:
            window_broadcasts: Number of recent broadcasts to analyze
            
        Returns:
            List of conflict pairs with details
        """
        from core.constants import CONTRADICTION_PAIRS
        
        recent = self.broadcasts[-window_broadcasts:] if window_broadcasts else self.broadcasts
        conflicts = []
        
        # Check for explicit CONFLICT broadcasts
        conflict_broadcasts = [b for b in recent if b['category'] == 'CONFLICT']
        for cb in conflict_broadcasts:
            conflicts.append({
                'type': 'explicit',
                'broadcast': cb,
                'reason': cb.get('content', 'Explicit conflict flagged')
            })
        
        # Check for contradictory broadcasts
        for i, b1 in enumerate(recent):
            for b2 in recent[i+1:]:
                # Skip if same agent (agents can change their minds)
                if b1['agent_alias'] == b2['agent_alias']:
                    continue
                    
                # Check if they're about the same topic
                if not self._same_topic(b1, b2):
                    continue
                
                # Check for contradictions
                is_contradictory, reason = self._are_contradictory(b1, b2)
                if is_contradictory:
                    conflict_id = str(uuid.uuid4())
                    conflict = {
                        'id': conflict_id,
                        'type': 'detected',
                        'broadcast1': b1,
                        'broadcast2': b2,
                        'reason': reason,
                        'detected_at': datetime.now(timezone.utc).isoformat()
                    }
                    conflicts.append(conflict)
                    self.conflicts.append(conflict)
        
        return conflicts
    
    def _are_contradictory(self, broadcast1: Dict, broadcast2: Dict) -> Tuple[bool, str]:
        """
        Check if two broadcasts contradict each other.
        
        Contradiction patterns:
        - (safe, unsafe), (secure, vulnerable)
        - (correct, incorrect), (valid, invalid)
        - (approve, reject), (yes, no)
        - (no issues, found issues)
        
        Args:
            broadcast1: First broadcast
            broadcast2: Second broadcast
            
        Returns:
            Tuple of (is_contradictory, reason)
        """
        from core.constants import CONTRADICTION_PAIRS
        
        content1 = broadcast1['content'].lower()
        content2 = broadcast2['content'].lower()
        
        for word1, word2 in CONTRADICTION_PAIRS:
            if word1 in content1 and word2 in content2:
                return True, f"Contradiction: '{word1}' vs '{word2}'"
            if word2 in content1 and word1 in content2:
                return True, f"Contradiction: '{word2}' vs '{word1}'"
        
        return False, ""
    
    def _same_topic(self, broadcast1: Dict, broadcast2: Dict) -> bool:
        """
        Check if two broadcasts are about the same topic.
        
        Args:
            broadcast1: First broadcast
            broadcast2: Second broadcast
            
        Returns:
            True if they're about the same topic
        """
        # Check if same category
        if broadcast1['category'] != broadcast2['category']:
            return False
        
        # Check metadata for file/function overlap
        meta1 = broadcast1.get('metadata', {})
        meta2 = broadcast2.get('metadata', {})
        
        # Check for overlapping files
        files1 = set(meta1.get('files', []))
        files2 = set(meta2.get('files', []))
        if files1 and files2 and files1.intersection(files2):
            return True
        
        # Check for overlapping functions
        funcs1 = set(meta1.get('functions', []))
        funcs2 = set(meta2.get('functions', []))
        if funcs1 and funcs2 and funcs1.intersection(funcs2):
            return True
        
        return False
    
    def flag_conflict(self, broadcast_ids: List[str], 
                     flagged_by: str, reason: str) -> Dict[str, Any]:
        """
        Manually flag broadcasts as conflicting.
        Creates a CONFLICT broadcast requiring arbitration.
        
        Args:
            broadcast_ids: List of conflicting broadcast IDs
            flagged_by: Agent alias who flagged the conflict
            reason: Reason for flagging as conflict
            
        Returns:
            Conflict record with details
        """
        conflict_id = str(uuid.uuid4())
        
        # Find the broadcasts
        broadcasts = [b for b in self.broadcasts if b['id'] in broadcast_ids]
        
        if len(broadcasts) != len(broadcast_ids):
            raise ValueError(f"Not all broadcast IDs found: {broadcast_ids}")
        
        conflict = {
            'id': conflict_id,
            'type': 'manual',
            'broadcasts': broadcasts,
            'flagged_by': flagged_by,
            'reason': reason,
            'flagged_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending_arbitration'
        }
        
        self.conflicts.append(conflict)
        
        # Create a CONFLICT category broadcast
        self.broadcast(
            agent_alias=flagged_by,
            agent_level=0,  # Will be updated with actual level
            category='CONFLICT',
            content=f"Conflict flagged: {reason}",
            metadata={
                'conflict_id': conflict_id,
                'broadcast_ids': broadcast_ids
            }
        )
        
        if self.db:
            self._persist_conflict(conflict)
        
        return conflict
    
    def get_conflicts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conflicts from the workspace.
        
        Args:
            status: Filter by status ('pending_arbitration', 'resolved', etc.)
            
        Returns:
            List of conflicts
        """
        if status:
            return [c for c in self.conflicts if c.get('status') == status]
        return self.conflicts
    
    def _persist_broadcast(self, broadcast: Dict[str, Any]) -> None:
        """Persist broadcast to database."""
        if not self.db:
            return
        
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT INTO broadcasts 
                    (broadcast_id, agent_alias, agent_level, category, content, metadata_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    broadcast['id'],
                    broadcast['agent_alias'],
                    broadcast['agent_level'],
                    broadcast['category'],
                    broadcast['content'],
                    json.dumps(broadcast.get('metadata', {})),
                    broadcast['timestamp']
                ))
                conn.commit()
        except Exception as e:
            # Log but don't fail on persistence errors
            print(f"Warning: Failed to persist broadcast: {e}")
    
    def _persist_conflict(self, conflict: Dict[str, Any]) -> None:
        """Persist conflict to database."""
        if not self.db:
            return
        
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                broadcast_ids = [b['id'] for b in conflict.get('broadcasts', [])]
                conn.execute("""
                    INSERT INTO conflicts
                    (conflict_id, conflict_type, broadcast_ids_json, flagged_by, reason, detected_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    conflict['id'],
                    conflict['type'],
                    json.dumps(broadcast_ids),
                    conflict.get('flagged_by', 'SYSTEM'),
                    conflict['reason'],
                    conflict.get('flagged_at') or conflict.get('detected_at'),
                    conflict.get('status', 'pending_arbitration')
                ))
                conn.commit()
        except Exception as e:
            # Log but don't fail on persistence errors
            print(f"Warning: Failed to persist conflict: {e}")
