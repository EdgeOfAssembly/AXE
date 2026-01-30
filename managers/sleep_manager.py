"""
Sleep Manager for AXE agents.
Manages mandatory sleep system for agents including:
- Tracking continuous work time (6-8 hour limit)
- Force sleep when degradation detected
- Graceful handover before sleep
- Resume from last state after rest
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from core.constants import SLEEP_REASON_TIMEOUT, SLEEP_REASON_DEGRADATION
from database.agent_db import AgentDatabase
class SleepManager:
    """
    Manages mandatory sleep system for agents.
    Features:
    - Track continuous work time (6-8 hour limit)
    - Force sleep when degradation detected
    - Graceful handover before sleep
    - Resume from last state after rest
    """
    def __init__(self, db: AgentDatabase):
        self.db = db
        self.sleep_queue: Dict[str, datetime] = {}  # agent_id -> wake_time
    def check_all_agents(self) -> List[Dict[str, Any]]:
        """Check all active agents for mandatory sleep requirements."""
        alerts = []
        active_agents = self.db.get_active_agents()
        for agent in active_agents:
            agent_id = agent['agent_id']
            # Check work time limit
            needs_sleep, msg = self.db.check_mandatory_sleep(agent_id)
            if needs_sleep:
                alerts.append({
                    'agent_id': agent_id,
                    'alias': agent['alias'],
                    'reason': SLEEP_REASON_TIMEOUT,
                    'message': msg
                })
                continue
            # Check degradation
            degraded, deg_msg = self.db.check_degradation(agent_id)
            if degraded:
                alerts.append({
                    'agent_id': agent_id,
                    'alias': agent['alias'],
                    'reason': SLEEP_REASON_DEGRADATION,
                    'message': deg_msg
                })
        return alerts
    def force_sleep(self, agent_id: str, reason: str,
                    supervisor_id: Optional[str] = None) -> Dict[str, Any]:
        """Force an agent to sleep."""
        result = self.db.put_agent_to_sleep(agent_id, reason)
        # Log the event
        if supervisor_id:
            self.db.log_supervisor_event(supervisor_id, 'force_sleep', {
                'agent_id': agent_id,
                'agent_alias': result['alias'],
                'reason': reason,
                'sleep_duration': result['sleep_duration_minutes']
            })
        # Track wake time
        wake_time = datetime.now(timezone.utc) + timedelta(minutes=result['sleep_duration_minutes'])
        self.sleep_queue[agent_id] = wake_time
        return result
    def check_and_wake_agents(self) -> List[Dict[str, Any]]:
        """Check for agents ready to wake up."""
        woken = []
        now = datetime.now(timezone.utc)
        to_remove = []
        for agent_id, wake_time in self.sleep_queue.items():
            if now >= wake_time:
                result = self.db.wake_agent(agent_id)
                woken.append(result)
                to_remove.append(agent_id)
        for agent_id in to_remove:
            del self.sleep_queue[agent_id]
        return woken
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all agent sleep statuses."""
        active = self.db.get_active_agents()
        sleeping = self.db.get_sleeping_agents()
        return {
            'active_count': len(active),
            'sleeping_count': len(sleeping),
            'active_agents': active,
            'sleeping_agents': sleeping,
            'pending_wakes': len(self.sleep_queue)
        }