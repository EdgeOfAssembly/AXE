"""
Arbitration Protocol for AXE conflict resolution.
Implements Marvin Minsky's cross-exclusion and conflict resolution patterns.
When agents disagree, conflicts are resolved through:
1. Automatic detection of contradictions
2. Escalation to higher-level agents
3. Structured arbitration with evidence
4. Binding resolution broadcast
Reference: Minsky, M. (1986). The Society of Mind. Chapters 17-19.
"""
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from core.constants import (
    ARBITRATION_DEADLINE_TURNS,
    ARBITRATION_AUTO_ESCALATE,
    ARBITRATION_MIN_LEVEL_BUMP
)
class ArbitrationProtocol:
    """
    Manages conflict detection, escalation, and resolution.
    Implements Minsky's concept of cross-exclusion where conflicting
    agents suppress each other until a higher-level agent resolves
    the conflict.
    """
    def __init__(self, global_workspace, subsumption_controller=None, db=None):
        """
        Initialize the arbitration protocol.
        Args:
            global_workspace: GlobalWorkspace instance for broadcasts
            subsumption_controller: Optional subsumption controller for hierarchical rules
            db: Optional AgentDatabase instance for persistence
        """
        self.workspace = global_workspace
        self.subsumption = subsumption_controller
        self.db = db
        self.pending_arbitrations: Dict[str, Dict] = {}
        self.resolved_arbitrations: List[Dict] = []
        self.current_turn = 0
    def create_arbitration(self, conflict_broadcasts: List[Dict],
                          created_by: str = 'SYSTEM') -> Dict[str, Any]:
        """
        Create an arbitration request for conflicting broadcasts.
        Args:
            conflict_broadcasts: List of conflicting broadcast dicts
            created_by: Who created the arbitration (agent alias or 'SYSTEM')
        Returns:
            Arbitration ticket with:
            - Unique ID
            - Conflicting broadcasts
            - Required arbitrator level
            - Deadline (turns)
        """
        arbitration_id = str(uuid.uuid4())
        # Find the highest level among conflicting agents
        max_level = max(b['agent_level'] for b in conflict_broadcasts)
        required_level = max_level + ARBITRATION_MIN_LEVEL_BUMP
        arbitration = {
            'id': arbitration_id,
            'conflict_broadcasts': conflict_broadcasts,
            'created_by': created_by,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'created_turn': self.current_turn,
            'deadline_turn': self.current_turn + ARBITRATION_DEADLINE_TURNS,
            'required_level': required_level,
            'status': 'pending',
            'escalation_count': 0,
        }
        self.pending_arbitrations[arbitration_id] = arbitration
        # Create a broadcast about the arbitration
        self.workspace.broadcast(
            agent_alias='SYSTEM',
            agent_level=999,  # System-level broadcast
            category='ARBITRATION',
            content=f"Arbitration created: requires level {required_level}+",
            metadata={
                'arbitration_id': arbitration_id,
                'required_level': required_level,
                'deadline_turn': arbitration['deadline_turn']
            }
        )
        if self.db:
            self._persist_arbitration(arbitration)
        return arbitration
    def get_arbitrator(self, arbitration_id: str,
                       available_agents: List[Dict]) -> Optional[Dict]:
        """
        Find the appropriate arbitrator for a conflict.
        Rules (Minsky's hierarchical principle):
        1. Must be higher level than all conflicting agents
        2. Must not be one of the conflicting agents
        3. Prefer lowest qualifying level (subsidiarity principle)
        Args:
            arbitration_id: ID of arbitration to resolve
            available_agents: List of agent dicts with 'alias' and 'level'
        Returns:
            Best arbitrator agent dict, or None if none qualified
        """
        if arbitration_id not in self.pending_arbitrations:
            return None
        arbitration = self.pending_arbitrations[arbitration_id]
        required_level = arbitration['required_level']
        # Get aliases of conflicting agents
        conflicting_aliases = {
            b['agent_alias'] for b in arbitration['conflict_broadcasts']
        }
        # Filter qualified arbitrators
        qualified = [
            agent for agent in available_agents
            if agent['level'] >= required_level
            and agent['alias'] not in conflicting_aliases
        ]
        if not qualified:
            return None
        # Return the lowest qualified level (subsidiarity)
        return min(qualified, key=lambda a: a['level'])
    def submit_resolution(self, arbitration_id: str,
                         arbitrator_alias: str, arbitrator_level: int,
                         resolution: str, winning_broadcast_id: str = None,
                         xp_awards: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Submit a resolution for an arbitration.
        Resolution can:
        - Declare a "winner" broadcast
        - Synthesize a new position
        - Award/penalize XP to participants
        - Suppress the "losing" agent temporarily
        Args:
            arbitration_id: ID of arbitration to resolve
            arbitrator_alias: Alias of arbitrating agent
            arbitrator_level: Level of arbitrating agent
            resolution: Resolution explanation/decision
            winning_broadcast_id: Optional ID of winning broadcast
            xp_awards: Optional dict of {agent_alias: xp_change}
        Returns:
            Resolution record with details
        """
        if arbitration_id not in self.pending_arbitrations:
            raise ValueError(f"Arbitration {arbitration_id} not found")
        arbitration = self.pending_arbitrations.pop(arbitration_id)
        # Verify arbitrator has sufficient level
        if arbitrator_level < arbitration['required_level']:
            raise ValueError(
                f"Arbitrator level {arbitrator_level} insufficient "
                f"(requires {arbitration['required_level']})"
            )
        # Create resolution record
        resolution_record = {
            'arbitration_id': arbitration_id,
            'arbitrator_alias': arbitrator_alias,
            'arbitrator_level': arbitrator_level,
            'resolution': resolution,
            'winning_broadcast_id': winning_broadcast_id,
            'resolved_at': datetime.now(timezone.utc).isoformat(),
            'resolved_turn': self.current_turn,
            'xp_awards': xp_awards or {},
        }
        # Update arbitration status
        arbitration['status'] = 'resolved'
        arbitration['resolution'] = resolution_record
        self.resolved_arbitrations.append(arbitration)
        # Broadcast the resolution
        self.workspace.broadcast(
            agent_alias=arbitrator_alias,
            agent_level=arbitrator_level,
            category='ARBITRATION_RESOLVED',
            content=f"Arbitration resolved: {resolution}",
            metadata={
                'arbitration_id': arbitration_id,
                'winning_broadcast_id': winning_broadcast_id,
                'xp_awards': xp_awards
            }
        )
        # Award XP through database if available
        if self.db and xp_awards:
            self._award_xp_to_agents(xp_awards)
        return resolution_record
    def get_pending_arbitrations(self,
                                 min_level: int = None) -> List[Dict]:
        """
        Get arbitrations pending resolution, optionally filtered by required level.
        Args:
            min_level: Optional minimum agent level to filter by
        Returns:
            List of pending arbitrations the agent can resolve
        """
        arbitrations = list(self.pending_arbitrations.values())
        if min_level is not None:
            arbitrations = [
                arb for arb in arbitrations
                if arb['required_level'] <= min_level
            ]
        return arbitrations
    def escalate_arbitration(self, arbitration_id: str,
                            reason: str) -> Dict[str, Any]:
        """
        Escalate an arbitration to a higher level.
        Used when:
        - Current level cannot resolve
        - Deadline expires without resolution
        - Arbitration deemed too complex
        Args:
            arbitration_id: ID of arbitration to escalate
            reason: Reason for escalation
        Returns:
            Updated arbitration record
        """
        if arbitration_id not in self.pending_arbitrations:
            raise ValueError(f"Arbitration {arbitration_id} not found")
        arbitration = self.pending_arbitrations[arbitration_id]
        # Increase required level
        old_level = arbitration['required_level']
        arbitration['required_level'] += ARBITRATION_MIN_LEVEL_BUMP
        arbitration['escalation_count'] += 1
        # Extend deadline
        arbitration['deadline_turn'] = self.current_turn + ARBITRATION_DEADLINE_TURNS
        # Record escalation
        if 'escalations' not in arbitration:
            arbitration['escalations'] = []
        arbitration['escalations'].append({
            'from_level': old_level,
            'to_level': arbitration['required_level'],
            'reason': reason,
            'escalated_at': datetime.now(timezone.utc).isoformat(),
            'escalated_turn': self.current_turn
        })
        # Broadcast escalation
        self.workspace.broadcast(
            agent_alias='SYSTEM',
            agent_level=999,
            category='ARBITRATION',
            content=f"Arbitration escalated to level {arbitration['required_level']}+: {reason}",
            metadata={
                'arbitration_id': arbitration_id,
                'new_required_level': arbitration['required_level'],
                'escalation_count': arbitration['escalation_count']
            }
        )
        if self.db:
            self._persist_arbitration(arbitration)
        return arbitration
    def check_deadlines(self) -> List[str]:
        """
        Check for arbitrations past their deadline and auto-escalate if enabled.
        Should be called each turn.
        Returns:
            List of escalated arbitration IDs
        """
        escalated = []
        for arb_id, arbitration in list(self.pending_arbitrations.items()):
            if self.current_turn >= arbitration['deadline_turn']:
                if ARBITRATION_AUTO_ESCALATE:
                    self.escalate_arbitration(
                        arb_id,
                        f"Deadline expired at turn {arbitration['deadline_turn']}"
                    )
                    escalated.append(arb_id)
        return escalated
    def format_for_prompt(self, agent_alias: str,
                         agent_level: int) -> str:
        """
        Format pending arbitrations for agent prompt.
        Only shows arbitrations the agent can resolve.
        Args:
            agent_alias: Alias of the agent
            agent_level: Level of the agent
        Returns:
            Formatted string for inclusion in agent prompt
        """
        eligible = self.get_pending_arbitrations(min_level=agent_level)
        if not eligible:
            return ""
        lines = ["\n**Pending Arbitrations You Can Resolve:**"]
        for arb in eligible:
            arb_id = arb['id'][:8]  # Short ID for display
            agents = ', '.join(
                b['agent_alias'] for b in arb['conflict_broadcasts']
            )
            lines.append(
                f"- [{arb_id}] {agents} disagree (requires level {arb['required_level']}+)"
            )
        lines.append(
            "\nTo resolve: [[ARBITRATE:{full_id}:Your resolution:winning_broadcast_id]]"
        )
        return "\n".join(lines)
    def increment_turn(self) -> None:
        """Increment the current turn counter."""
        self.current_turn += 1
        self.check_deadlines()
    def _persist_arbitration(self, arbitration: Dict[str, Any]) -> None:
        """Persist arbitration to database."""
        if not self.db:
            return
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO arbitrations
                    (arbitration_id, conflict_broadcasts_json, created_by, created_at,
                     created_turn, deadline_turn, required_level, status, escalation_count,
                     resolution_json, resolved_at, resolved_turn)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    arbitration['id'],
                    json.dumps([b['id'] for b in arbitration['conflict_broadcasts']]),
                    arbitration['created_by'],
                    arbitration['created_at'],
                    arbitration['created_turn'],
                    arbitration['deadline_turn'],
                    arbitration['required_level'],
                    arbitration['status'],
                    arbitration['escalation_count'],
                    json.dumps(arbitration.get('resolution')) if arbitration.get('resolution') else None,
                    arbitration.get('resolved_at'),
                    arbitration.get('resolved_turn')
                ))
                conn.commit()
        except Exception as e:
            # Log but don't fail on persistence errors
            print(f"Warning: Failed to persist arbitration: {e}")
    def _award_xp_to_agents(self, xp_awards: Dict[str, int]) -> None:
        """
        Award XP to agents through the database.
        Args:
            xp_awards: Dict of {agent_alias: xp_change}
        """
        if not self.db:
            return
        for alias, xp_change in xp_awards.items():
            try:
                # Get current agent state
                agent = self.db.get_agent_by_alias(alias)
                if agent:
                    current_xp = agent.get('xp', 0)
                    new_xp = max(0, current_xp + xp_change)  # Don't go negative
                    # Update XP
                    self.db.update_agent_xp(alias, new_xp)
            except Exception as e:
                # Log but don't fail on XP award errors
                print(f"Warning: Failed to award XP to {alias}: {e}")