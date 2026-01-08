"""
Break System for AXE agents.

Manages coffee/play breaks for agents with the following rules:
- Only when workload is low (<30% utilization)
- Max 10-15 min per break
- Max 2 breaks per hour
- Never more than 40% of workforce on break
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

from core.constants import MAX_BREAK_MINUTES
from database.agent_db import AgentDatabase


class BreakSystem:
    """
    Manages coffee/play breaks for agents.

    Rules:
    - Only when workload is low (<30% utilization)
    - Max 10-15 min per break
    - Max 2 breaks per hour
    - Never more than 40% of workforce on break
    """

    def __init__(self, db: AgentDatabase):
        self.db = db
        self.break_queue: Dict[str, datetime] = {}  # agent_id -> break_end_time
        self.pending_requests: List[Dict[str, Any]] = []

    def request_break(self, agent_id: str, alias: str,
                      break_type: str, justification: str) -> Dict[str, Any]:
        """
        Request a break for an agent.

        Args:
            agent_id: Unique agent identifier
            alias: Agent's display alias
            break_type: 'coffee' or 'play'
            justification: Why the agent needs a break

        Returns:
            Request status and details
        """
        request = {
            'id': str(uuid.uuid4()),
            'agent_id': agent_id,
            'alias': alias,
            'break_type': break_type,
            'justification': justification,
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending'
        }

        self.pending_requests.append(request)

        return request

    def approve_break(self, request_id: str, duration_minutes: int = 10,
                      supervisor_alias: str = "@boss") -> Dict[str, Any]:
        """Approve a pending break request."""
        # Find the request
        request = None
        for req in self.pending_requests:
            if req['id'] == request_id:
                request = req
                break

        if not request:
            return {'approved': False, 'reason': 'Request not found'}

        agent_id = request['agent_id']

        # Check if break is allowed
        total_agents = len(self.db.get_active_agents()) + len(self.break_queue)
        agents_on_break = len(self.break_queue)

        can_break, reason = self.db.can_take_break(agent_id, total_agents, agents_on_break)

        if not can_break:
            request['status'] = 'denied'
            request['deny_reason'] = reason
            return {'approved': False, 'reason': reason}

        # Cap duration
        duration_minutes = min(duration_minutes, MAX_BREAK_MINUTES)

        # Record the break
        self.db.record_break(agent_id, request['break_type'], duration_minutes)

        # Set break end time
        end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self.break_queue[agent_id] = end_time

        # Update request status
        request['status'] = 'approved'
        request['approved_by'] = supervisor_alias
        request['duration_minutes'] = duration_minutes
        request['ends_at'] = end_time.isoformat()

        return {
            'approved': True,
            'agent_id': agent_id,
            'alias': request['alias'],
            'break_type': request['break_type'],
            'duration_minutes': duration_minutes,
            'ends_at': end_time.isoformat()
        }

    def deny_break(self, request_id: str, reason: str) -> Dict[str, Any]:
        """Deny a pending break request."""
        for request in self.pending_requests:
            if request['id'] == request_id:
                request['status'] = 'denied'
                request['deny_reason'] = reason
                return {'denied': True, 'request_id': request_id, 'reason': reason}

        return {'denied': False, 'reason': 'Request not found'}

    def check_break_endings(self) -> List[Dict[str, Any]]:
        """Check for breaks that have ended."""
        ended = []
        now = datetime.now(timezone.utc)

        to_remove = []
        for agent_id, end_time in self.break_queue.items():
            if now >= end_time:
                ended.append({
                    'agent_id': agent_id,
                    'break_ended': now.isoformat()
                })
                to_remove.append(agent_id)

        for agent_id in to_remove:
            del self.break_queue[agent_id]

        return ended

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending break requests."""
        return [r for r in self.pending_requests if r['status'] == 'pending']

    def get_status(self) -> Dict[str, Any]:
        """Get current break system status."""
        return {
            'agents_on_break': len(self.break_queue),
            'pending_requests': len(self.get_pending_requests()),
            'on_break': list(self.break_queue.keys())
        }
