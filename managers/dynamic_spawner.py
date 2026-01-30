"""
Dynamic Spawner for AXE agents.
Manages dynamic spawning of agents based on workload and resources.
Features:
- Spawn new agent instances on demand
- Resource-based spawning decisions
- Auto-scaling based on task complexity
- Spawn cooldown to prevent rapid creation
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from core.constants import (
    SPAWN_COOLDOWN_SECONDS,
    MAX_TOTAL_AGENTS,
    MIN_ACTIVE_AGENTS
)
from database.agent_db import AgentDatabase
if TYPE_CHECKING:
    from core.config import Config
class DynamicSpawner:
    """
    Manages dynamic spawning of agents based on workload and resources.
    Features:
    - Spawn new agent instances on demand
    - Resource-based spawning decisions
    - Auto-scaling based on task complexity
    - Spawn cooldown to prevent rapid creation
    """
    def __init__(self, db: AgentDatabase, config: 'Config'):
        self.db = db
        self.config = config
        self.last_spawn_time: Optional[datetime] = None
        self.spawn_history: List[Dict[str, Any]] = []
    def can_spawn(self) -> Tuple[bool, str]:
        """Check if a new agent can be spawned."""
        # Check cooldown
        if self.last_spawn_time:
            elapsed = (datetime.now(timezone.utc) - self.last_spawn_time).total_seconds()
            if elapsed < SPAWN_COOLDOWN_SECONDS:
                remaining = SPAWN_COOLDOWN_SECONDS - elapsed
                return False, f"Spawn cooldown: {remaining:.0f}s remaining"
        # Check total agent limit
        active = self.db.get_active_agents()
        sleeping = self.db.get_sleeping_agents()
        total = len(active) + len(sleeping)
        if total >= MAX_TOTAL_AGENTS:
            return False, f"Maximum agent limit ({MAX_TOTAL_AGENTS}) reached"
        return True, "Spawn allowed"
    def spawn_agent(self, model_name: str, provider: str,
                    supervisor_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Spawn a new agent instance.
        Args:
            model_name: The model to use for the new agent
            provider: API provider (openai, anthropic, etc.)
            supervisor_id: ID of the supervisor requesting spawn
            reason: Why the agent is being spawned
        Returns:
            New agent info or error
        """
        can, msg = self.can_spawn()
        if not can:
            return {'spawned': False, 'reason': msg}
        # Generate unique ID and alias
        agent_id = str(uuid.uuid4())
        clean_model = model_name.replace('/', '-').replace('.', '-')
        agent_num = self.db.get_next_agent_number(clean_model)
        alias = f"@{clean_model}{agent_num}"
        # Create agent in database
        self.db.save_agent_state(
            agent_id=agent_id,
            alias=alias,
            model_name=model_name,
            memory_dict={'spawned_by': supervisor_id, 'spawn_reason': reason},
            diffs=[],
            error_count=0,
            xp=0,
            level=1,
            supervisor_id=supervisor_id
        )
        # Start work tracking
        self.db.start_work_tracking(agent_id)
        # Record spawn
        self.last_spawn_time = datetime.now(timezone.utc)
        spawn_record = {
            'agent_id': agent_id,
            'alias': alias,
            'model_name': model_name,
            'provider': provider,
            'spawned_at': self.last_spawn_time.isoformat(),
            'spawned_by': supervisor_id,
            'reason': reason
        }
        self.spawn_history.append(spawn_record)
        # Log event
        self.db.log_supervisor_event(supervisor_id, 'spawn_agent', spawn_record)
        return {
            'spawned': True,
            'agent_id': agent_id,
            'alias': alias,
            'model_name': model_name,
            'provider': provider
        }
    def should_auto_spawn(self, task_complexity: float = 0.5) -> Tuple[bool, str]:
        """
        Determine if auto-spawning is needed based on workload.
        Args:
            task_complexity: 0.0-1.0 scale of task complexity
        Returns:
            Tuple of (should_spawn, reason)
        """
        active = self.db.get_active_agents()
        # Check for recent failed spawn attempts to prevent infinite loops
        recent_failures = sum(1 for s in self.spawn_history[-5:] if not s.get('spawned', True))
        if recent_failures >= 3:
            return False, "Too many recent spawn failures, pausing auto-spawn"
        # Ensure minimum active agents
        if len(active) < MIN_ACTIVE_AGENTS:
            return True, f"Below minimum active agents ({len(active)} < {MIN_ACTIVE_AGENTS})"
        # High complexity tasks may benefit from more agents
        if task_complexity > 0.7 and len(active) < 5:
            return True, f"High complexity task ({task_complexity:.0%}) may benefit from more agents"
        return False, "No auto-spawn needed"
    def get_spawn_history(self) -> List[Dict[str, Any]]:
        """Get recent spawn history."""
        return self.spawn_history[-20:]  # Last 20 spawns