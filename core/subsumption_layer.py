"""
Subsumption Architecture Controller for AXE (Brooks 1986).

Implements Rodney Brooks' Subsumption Architecture for layered agent execution:
- Agents are organized in behavioral layers
- Higher layers can suppress lower layers when needed
- Lower layers continue to function if higher layers fail
- No central world model - coordination emerges from layer interactions

Reference: Brooks, R. A. (1986). A Robust Layered Control System for a Mobile Robot.
MIT AI Lab. https://people.csail.mit.edu/brooks/papers/AIM-864.pdf
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import IntEnum

from progression.levels import (
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE,
)
from core.constants import SUPPRESSION_DEFAULT_TURNS, SUPPRESSION_MAX_TURNS


class SubsumptionLayer(IntEnum):
    """
    Subsumption layers mapping AXE levels to Brooks-style behavioral layers.
    
    Lower layers handle basic "survival" behaviors, higher layers handle
    strategic planning. Higher layers can suppress lower layers when needed.
    """
    SURVIVAL = 0    # System-level (always runs) - token limits, security, degradation
    WORKER = 1      # Levels 1-9 - basic task execution
    TACTICAL = 2    # Levels 10-19 - Senior Worker, Team Leader
    STRATEGIC = 3   # Levels 20-29 - Deputy Supervisor
    EXECUTIVE = 4   # Levels 30+ - Supervisor-Eligible


# Layer metadata for prompts and descriptions
LAYER_METADATA = {
    SubsumptionLayer.SURVIVAL: {
        "name": "Survival",
        "description": "System-level safety and degradation handling",
        "responsibilities": [
            "Monitor token limits",
            "Enforce security policies",
            "Handle degradation and emergency shutdown"
        ]
    },
    SubsumptionLayer.WORKER: {
        "name": "Worker",
        "description": "Basic task execution",
        "responsibilities": [
            "Execute assigned tasks",
            "Follow instructions from higher layers",
            "Report status and progress"
        ]
    },
    SubsumptionLayer.TACTICAL: {
        "name": "Tactical",
        "description": "Task coordination and team management",
        "responsibilities": [
            "Coordinate multiple tasks",
            "Manage worker agents",
            "Optimize execution strategies"
        ]
    },
    SubsumptionLayer.STRATEGIC: {
        "name": "Strategic",
        "description": "High-level planning and resource allocation",
        "responsibilities": [
            "Plan long-term objectives",
            "Allocate resources across teams",
            "Make architectural decisions"
        ]
    },
    SubsumptionLayer.EXECUTIVE: {
        "name": "Executive",
        "description": "System-wide supervision and policy",
        "responsibilities": [
            "Set system-wide policies",
            "Supervise all lower layers",
            "Handle escalations and conflicts"
        ]
    }
}


@dataclass
class Suppression:
    """
    Represents an active suppression of one agent by another.
    """
    suppressor_id: str
    suppressor_level: int
    target_id: str
    target_level: int
    reason: str
    turns_remaining: int
    created_at: str
    
    def tick(self) -> bool:
        """
        Decrement turns_remaining by 1.
        
        Returns:
            True if suppression is still active, False if expired
        """
        self.turns_remaining -= 1
        return self.turns_remaining > 0


class SubsumptionController:
    """
    Controller for subsumption architecture in AXE.
    
    Manages layered agent execution with suppression capabilities.
    """
    
    def __init__(self):
        """Initialize the subsumption controller."""
        # Maps target_agent_id -> Suppression
        self.active_suppressions: Dict[str, Suppression] = {}
        
        # Optional GlobalWorkspace integration (from PR #38)
        self.global_workspace = None
    
    def set_global_workspace(self, workspace):
        """
        Set GlobalWorkspace for broadcasting suppression events.
        
        Args:
            workspace: GlobalWorkspace instance (optional)
        """
        self.global_workspace = workspace
    
    @staticmethod
    def get_layer_for_level(level: int) -> SubsumptionLayer:
        """
        Map an agent's XP level to a subsumption layer.
        
        Args:
            level: Agent's XP level (1-50+)
        
        Returns:
            SubsumptionLayer enum value
        """
        if level >= LEVEL_SUPERVISOR_ELIGIBLE:  # 40+
            return SubsumptionLayer.EXECUTIVE
        elif level >= LEVEL_DEPUTY_SUPERVISOR:  # 30-39
            return SubsumptionLayer.STRATEGIC
        elif level >= LEVEL_SENIOR_WORKER:     # 10-29
            # Split 10-29 range: 10-19 = TACTICAL, 20-29 = STRATEGIC
            if level < LEVEL_TEAM_LEADER:       # 10-19
                return SubsumptionLayer.TACTICAL
            else:                                # 20-29
                return SubsumptionLayer.STRATEGIC
        else:                                    # 1-9
            return SubsumptionLayer.WORKER
    
    def can_suppress(self, suppressor_level: int, target_level: int) -> bool:
        """
        Check if an agent can suppress another based on their levels.
        
        Higher layers can suppress lower layers. Agents at the same layer
        cannot suppress each other (prevents conflicts).
        
        Args:
            suppressor_level: XP level of the suppressing agent
            target_level: XP level of the target agent
        
        Returns:
            True if suppression is allowed, False otherwise
        """
        suppressor_layer = self.get_layer_for_level(suppressor_level)
        target_layer = self.get_layer_for_level(target_level)
        
        # Can only suppress agents in lower layers
        return suppressor_layer > target_layer
    
    def suppress_agent(
        self,
        suppressor_id: str,
        suppressor_level: int,
        target_id: str,
        target_level: int,
        reason: str,
        turns: int = SUPPRESSION_DEFAULT_TURNS
    ) -> Tuple[bool, str]:
        """
        Suppress a target agent for N turns.
        
        Args:
            suppressor_id: ID/alias of suppressing agent
            suppressor_level: XP level of suppressing agent
            target_id: ID/alias of target agent
            target_level: XP level of target agent
            reason: Human-readable reason for suppression
            turns: Number of turns to suppress (default: SUPPRESSION_DEFAULT_TURNS)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate permission
        if not self.can_suppress(suppressor_level, target_level):
            suppressor_layer = self.get_layer_for_level(suppressor_level)
            target_layer = self.get_layer_for_level(target_level)
            return (
                False,
                f"Agent {suppressor_id} (Layer {suppressor_layer.value}) "
                f"cannot suppress {target_id} (Layer {target_layer.value}). "
                f"Can only suppress lower layers."
            )
        
        # Enforce max turns
        turns = min(turns, SUPPRESSION_MAX_TURNS)
        
        # Create suppression
        suppression = Suppression(
            suppressor_id=suppressor_id,
            suppressor_level=suppressor_level,
            target_id=target_id,
            target_level=target_level,
            reason=reason,
            turns_remaining=turns,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self.active_suppressions[target_id] = suppression
        
        # Broadcast to GlobalWorkspace if available
        if self.global_workspace:
            try:
                self.global_workspace.broadcast(
                    category="STATUS",
                    content={
                        "type": "suppression_created",
                        "suppressor": suppressor_id,
                        "target": target_id,
                        "reason": reason,
                        "turns": turns
                    },
                    source=suppressor_id
                )
            except Exception:
                # GlobalWorkspace is optional, don't fail if it errors
                pass
        
        suppressor_layer = self.get_layer_for_level(suppressor_level)
        target_layer = self.get_layer_for_level(target_level)
        return (
            True,
            f"✓ {suppressor_id} (L{suppressor_layer.value}) suppressed "
            f"{target_id} (L{target_layer.value}) for {turns} turns: {reason}"
        )
    
    def release_suppression(
        self,
        releaser_id: str,
        releaser_level: int,
        target_id: str
    ) -> Tuple[bool, str]:
        """
        Manually release a suppression.
        
        Only the original suppressor or a higher-layer agent can release.
        
        Args:
            releaser_id: ID/alias of agent releasing suppression
            releaser_level: XP level of releasing agent
            target_id: ID/alias of suppressed agent
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if target_id not in self.active_suppressions:
            return False, f"Agent {target_id} is not currently suppressed."
        
        suppression = self.active_suppressions[target_id]
        
        # Check permission: must be original suppressor or higher layer
        releaser_layer = self.get_layer_for_level(releaser_level)
        suppressor_layer = self.get_layer_for_level(suppression.suppressor_level)
        
        is_original_suppressor = releaser_id == suppression.suppressor_id
        is_higher_layer = releaser_layer > suppressor_layer
        
        if not (is_original_suppressor or is_higher_layer):
            return (
                False,
                f"Agent {releaser_id} (L{releaser_layer.value}) cannot release "
                f"suppression created by {suppression.suppressor_id} (L{suppressor_layer.value}). "
                f"Only the original suppressor or a higher layer can release."
            )
        
        # Release suppression
        del self.active_suppressions[target_id]
        
        # Broadcast to GlobalWorkspace if available
        if self.global_workspace:
            try:
                self.global_workspace.broadcast(
                    category="STATUS",
                    content={
                        "type": "suppression_released",
                        "releaser": releaser_id,
                        "target": target_id,
                        "original_suppressor": suppression.suppressor_id
                    },
                    source=releaser_id
                )
            except Exception:
                pass
        
        return True, f"✓ Released suppression on {target_id}"
    
    def tick_suppressions(self) -> List[str]:
        """
        Decrement all active suppressions by 1 turn.
        
        Should be called at the end of each collaboration turn.
        
        Returns:
            List of agent IDs whose suppressions expired this turn
        """
        expired = []
        
        for target_id, suppression in list(self.active_suppressions.items()):
            if not suppression.tick():
                expired.append(target_id)
                del self.active_suppressions[target_id]
                
                # Broadcast expiration
                if self.global_workspace:
                    try:
                        self.global_workspace.broadcast(
                            category="STATUS",
                            content={
                                "type": "suppression_expired",
                                "target": target_id,
                                "original_suppressor": suppression.suppressor_id
                            },
                            source="system"
                        )
                    except Exception:
                        pass
        
        return expired
    
    def is_suppressed(self, agent_id: str) -> bool:
        """
        Check if an agent is currently suppressed.
        
        Args:
            agent_id: Agent ID/alias to check
        
        Returns:
            True if agent is suppressed, False otherwise
        """
        return agent_id in self.active_suppressions
    
    def get_suppression_info(self, agent_id: str) -> Optional[Suppression]:
        """
        Get suppression info for an agent.
        
        Args:
            agent_id: Agent ID/alias
        
        Returns:
            Suppression object if suppressed, None otherwise
        """
        return self.active_suppressions.get(agent_id)
    
    def get_execution_order(self, agents: List[Dict]) -> List[Dict]:
        """
        Sort agents by subsumption layer (highest first), excluding suppressed agents.
        
        Args:
            agents: List of agent dicts with at minimum 'id' and 'level' keys
        
        Returns:
            Sorted list of non-suppressed agents (highest layer first)
        """
        # Filter out suppressed agents
        active_agents = [
            agent for agent in agents
            if not self.is_suppressed(agent.get('id', agent.get('alias', '')))
        ]
        
        # Sort by layer (highest first), then by level within layer
        def sort_key(agent):
            level = agent.get('level', 1)
            layer = self.get_layer_for_level(level)
            # Return negative to sort descending
            return (-layer.value, -level)
        
        return sorted(active_agents, key=sort_key)
    
    def format_for_prompt(self, agent_alias: str, level: int) -> str:
        """
        Format subsumption layer information for agent prompt.
        
        Args:
            agent_alias: Agent's alias/ID
            level: Agent's XP level
        
        Returns:
            Formatted string for prompt injection
        """
        layer = self.get_layer_for_level(level)
        metadata = LAYER_METADATA[layer]
        
        # Determine what this agent can suppress
        can_suppress_layers = []
        for check_layer in SubsumptionLayer:
            if layer > check_layer:
                can_suppress_layers.append(LAYER_METADATA[check_layer]["name"])
        
        # Determine what can suppress this agent
        can_be_suppressed_by = []
        for check_layer in SubsumptionLayer:
            if check_layer > layer:
                can_be_suppressed_by.append(LAYER_METADATA[check_layer]["name"])
        
        # Check if currently suppressed
        suppression_status = ""
        if self.is_suppressed(agent_alias):
            supp = self.active_suppressions[agent_alias]
            suppression_status = f"\n**Currently Suppressed:** Yes (by {supp.suppressor_id} for {supp.turns_remaining} more turns)\n  Reason: {supp.reason}"
        
        # Build prompt section
        prompt = f"""## YOUR SUBSUMPTION LAYER: {metadata['name']} (Layer {layer.value})

**Your Responsibilities:**
{chr(10).join(f'  - {resp}' for resp in metadata['responsibilities'])}
"""
        
        if can_suppress_layers:
            prompt += f"""
**You CAN suppress:** {', '.join(can_suppress_layers)} 
Use: [[SUPPRESS:@agent_alias:reason]] to suppress for {SUPPRESSION_DEFAULT_TURNS} turns
"""
        
        if can_be_suppressed_by:
            prompt += f"""
**You CAN BE suppressed by:** {', '.join(can_be_suppressed_by)}
"""
        
        if suppression_status:
            prompt += suppression_status
        
        return prompt
