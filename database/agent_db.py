"""
Database operations for agent state persistence.
Thread-safe SQLite operations with WAL mode.
"""

import os
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple, Any

# Import from local modules
from .schema import (
    AGENT_STATE_TABLE,
    AGENT_STATE_MIGRATIONS,
    SUPERVISOR_LOG_TABLE,
    ALIAS_MAPPINGS_TABLE,
    WAL_MODE_PRAGMA
)


def get_database_path() -> str:
    """Get the path to the AXE database file.
    
    Always uses the AXE installation directory, NOT the workspace.
    This ensures agent XP, levels, and history persist across sessions.
    
    Returns:
        Absolute path to axe_agents.db in the AXE installation directory
    """
    # Get the directory where this file (agent_db.py) is located
    # which is the database/ subdirectory of the AXE installation
    database_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the AXE installation root
    axe_dir = os.path.dirname(database_dir)
    return os.path.join(axe_dir, "axe_agents.db")


class AgentDatabase:
    """SQLite database manager for agent state, memory, and progression."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Optional path override. If None, uses AXE installation directory.
        """
        if db_path is None:
            db_path = get_database_path()
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema with migrations."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrency
            conn.execute(WAL_MODE_PRAGMA)
            
            c = conn.cursor()
            
            # Create tables
            c.execute(AGENT_STATE_TABLE)
            c.execute(SUPERVISOR_LOG_TABLE)
            c.execute(ALIAS_MAPPINGS_TABLE)
            
            # Apply migrations for existing databases
            self._apply_migrations(conn)
            
            conn.commit()
    
    def _apply_migrations(self, conn: sqlite3.Connection) -> None:
        """Apply schema migrations to existing tables."""
        c = conn.cursor()
        
        # Check which columns exist in agent_state
        c.execute("PRAGMA table_info(agent_state)")
        existing_columns = {row[1] for row in c.fetchall()}
        
        # Apply migrations for missing columns
        for migration in AGENT_STATE_MIGRATIONS:
            # Extract column name from ALTER TABLE statement
            if "ADD COLUMN" in migration:
                column_name = migration.split("ADD COLUMN")[1].split()[0]
                if column_name not in existing_columns:
                    try:
                        c.execute(migration)
                    except sqlite3.OperationalError:
                        # Column might already exist, skip
                        pass
    
    def save_agent_state(self, agent_id: str, alias: str, model_name: str,
                        memory_dict: Dict[str, Any], diffs: List[str], 
                        error_count: int, xp: int, level: int,
                        supervisor_id: str = None) -> None:
        """Save agent state to database."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO agent_state 
                (agent_id, alias, model_name, supervisor_id, last_updated, 
                 memory_json, recent_diffs, error_count, xp, level, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_id,
                alias,
                model_name,
                supervisor_id,
                datetime.now(timezone.utc),
                json.dumps(memory_dict),
                json.dumps(diffs[-10:]),  # Keep last 10 diffs
                error_count,
                xp,
                level,
                'active'
            ))
            conn.commit()
    
    def load_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state from database."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT alias, model_name, memory_json, recent_diffs, 
                       error_count, xp, level, status
                FROM agent_state WHERE agent_id = ?
            ''', (agent_id,))
            row = c.fetchone()
            
            if row:
                return {
                    'alias': row[0],
                    'model_name': row[1],
                    'memory': json.loads(row[2]),
                    'diffs': json.loads(row[3]),
                    'error_count': row[4],
                    'xp': row[5],
                    'level': row[6],
                    'status': row[7]
                }
        return None
    
    def get_next_agent_number(self, model_name: str) -> int:
        """Get the next available number for an agent alias."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Extract number from aliases like @llama1, @llama2, etc.
            c.execute('''
                SELECT alias FROM agent_state 
                WHERE alias LIKE ?
            ''', (f'@{model_name}%',))
            
            aliases = [row[0] for row in c.fetchall()]
            
            if not aliases:
                return 1
            
            # Extract numbers and find max
            numbers = []
            for alias in aliases:
                # Remove @ prefix and model name, leaving just the number
                try:
                    num_str = alias.replace(f'@{model_name}', '')
                    if num_str:
                        numbers.append(int(num_str))
                except ValueError:
                    continue
            
            return max(numbers) + 1 if numbers else 1
    
    def award_xp(self, agent_id: str, xp_amount: int, reason: str = "") -> Dict[str, Any]:
        """
        Award XP to an agent and handle level-ups.
        Note: This method imports from progression module to avoid circular imports.
        """
        # Import here to avoid circular dependency
        from progression.xp_system import calculate_xp_for_level
        from progression.levels import get_title_for_level, LEVEL_SUPERVISOR_ELIGIBLE
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT xp, level, alias FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if not row:
                return {'leveled_up': False, 'message': 'Agent not found'}
            
            old_xp, old_level, alias = row
            new_xp = old_xp + xp_amount
            
            # Calculate new level
            new_level = old_level
            while new_level < LEVEL_SUPERVISOR_ELIGIBLE:
                xp_needed = calculate_xp_for_level(new_level + 1)
                if new_xp >= xp_needed:
                    new_level += 1
                else:
                    break
            
            # Update database
            c.execute('''
                UPDATE agent_state SET xp = ?, level = ?, last_updated = ?
                WHERE agent_id = ?
            ''', (new_xp, new_level, datetime.now(timezone.utc), agent_id))
            conn.commit()
            
            result = {
                'leveled_up': new_level > old_level,
                'old_level': old_level,
                'new_level': new_level,
                'xp': new_xp,
                'alias': alias,
                'reason': reason
            }
            
            if result['leveled_up']:
                result['new_title'] = get_title_for_level(new_level)
            
            return result
    
    def log_supervisor_event(self, supervisor_id: str, event_type: str, 
                            details: Dict[str, Any]) -> None:
        """Log a supervisor decision or event."""
        log_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO supervisor_log (log_id, supervisor_id, timestamp, event_type, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (log_id, supervisor_id, datetime.now(timezone.utc), event_type, json.dumps(details)))
            conn.commit()
    
    def alias_exists(self, alias: str) -> bool:
        """Check if an alias already exists."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM agent_state WHERE alias = ?', (alias,))
            return c.fetchone()[0] > 0
    
    # ========== Phase 6: Mandatory Sleep System ==========
    
    def start_work_tracking(self, agent_id: str) -> None:
        """Start tracking work time for an agent."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE agent_state SET work_start_time = ?, status = 'active'
                WHERE agent_id = ?
            ''', (datetime.now(timezone.utc), agent_id))
            conn.commit()
    
    def get_work_duration_minutes(self, agent_id: str) -> int:
        """Get how many minutes the agent has been working continuously."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT work_start_time FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row and row[0]:
                try:
                    start_time = datetime.fromisoformat(row[0])
                    elapsed = datetime.now(timezone.utc) - start_time
                    return int(elapsed.total_seconds() / 60)
                except (ValueError, TypeError):
                    return 0
        return 0
    
    def put_agent_to_sleep(self, agent_id: str, reason: str, duration_minutes: int = 30) -> Dict[str, Any]:
        """
        Put an agent to sleep and record the event.
        Note: MIN_SLEEP_MINUTES is hardcoded here as 30 to avoid circular import.
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Get current work duration before sleeping
            work_duration = self.get_work_duration_minutes(agent_id)
            
            # Update agent status
            sleep_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            c.execute('''
                UPDATE agent_state 
                SET status = 'sleeping', 
                    work_start_time = NULL,
                    total_work_minutes = total_work_minutes + ?
                WHERE agent_id = ?
            ''', (work_duration, agent_id))
            
            # Get agent alias for logging
            c.execute('SELECT alias FROM agent_state WHERE agent_id = ?', (agent_id,))
            alias_row = c.fetchone()
            alias = alias_row[0] if alias_row else agent_id
            
            conn.commit()
            
            return {
                'agent_id': agent_id,
                'alias': alias,
                'reason': reason,
                'work_duration_minutes': work_duration,
                'sleep_duration_minutes': duration_minutes,
                'sleep_until': sleep_until.isoformat()
            }
    
    def wake_agent(self, agent_id: str) -> Dict[str, Any]:
        """Wake an agent from sleep."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE agent_state 
                SET status = 'active', work_start_time = ?
                WHERE agent_id = ?
            ''', (datetime.now(timezone.utc), agent_id))
            
            # Get agent alias
            c.execute('SELECT alias FROM agent_state WHERE agent_id = ?', (agent_id,))
            alias_row = c.fetchone()
            alias = alias_row[0] if alias_row else agent_id
            
            conn.commit()
            
            return {
                'agent_id': agent_id,
                'alias': alias,
                'status': 'active',
                'woke_at': datetime.now(timezone.utc).isoformat()
            }
    
    def get_sleeping_agents(self) -> List[Dict[str, Any]]:
        """Get list of all sleeping agents."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT agent_id, alias, model_name, total_work_minutes 
                FROM agent_state WHERE status = 'sleeping'
            ''')
            rows = c.fetchall()
            
            return [
                {
                    'agent_id': row[0],
                    'alias': row[1],
                    'model_name': row[2],
                    'total_work_minutes': row[3]
                }
                for row in rows
            ]
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of all active agents."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT agent_id, alias, model_name, work_start_time, xp, level
                FROM agent_state WHERE status = 'active'
            ''')
            rows = c.fetchall()
            
            return [
                {
                    'agent_id': row[0],
                    'alias': row[1],
                    'model_name': row[2],
                    'work_start_time': row[3],
                    'xp': row[4],
                    'level': row[5]
                }
                for row in rows
            ]
    
    def check_mandatory_sleep(self, agent_id: str, max_work_hours: int = 6, 
                             warning_hours: int = 5) -> Tuple[bool, str]:
        """
        Check if agent needs mandatory sleep due to work time limit.
        Note: Constants are parameters to avoid circular import.
        """
        work_minutes = self.get_work_duration_minutes(agent_id)
        work_hours = work_minutes / 60
        
        if work_hours >= max_work_hours:
            return True, f"Work time limit reached ({work_hours:.1f} hours)"
        elif work_hours >= warning_hours:
            remaining = max_work_hours - work_hours
            return False, f"Warning: {remaining:.1f} hours until mandatory sleep"
        
        return False, ""
    
    # ========== Phase 7: Degradation Monitoring ==========
    
    def record_diff(self, agent_id: str, diff_content: str, error_count: int = 0,
                   diff_history_limit: int = 20) -> None:
        """
        Record a code diff and its error count for an agent.
        Note: DIFF_HISTORY_LIMIT is a parameter to avoid circular import.
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Get existing diffs
            c.execute('SELECT recent_diffs, error_count FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row:
                try:
                    diffs = json.loads(row[0]) if row[0] else []
                except json.JSONDecodeError:
                    diffs = []
                
                current_errors = row[1] or 0
                
                # Add new diff with timestamp and error info
                diff_record = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'content_hash': hashlib.sha256(diff_content.encode()).hexdigest()[:16],
                    'errors': error_count,
                    'size': len(diff_content)
                }
                diffs.append(diff_record)
                
                # Keep only the last N diffs
                diffs = diffs[-diff_history_limit:]
                
                # Update database
                c.execute('''
                    UPDATE agent_state 
                    SET recent_diffs = ?, error_count = ?, last_updated = ?
                    WHERE agent_id = ?
                ''', (json.dumps(diffs), current_errors + error_count, datetime.now(timezone.utc), agent_id))
                conn.commit()
    
    def get_error_rate(self, agent_id: str) -> float:
        """Calculate error rate from recent diffs."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT recent_diffs FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row and row[0]:
                try:
                    diffs = json.loads(row[0])
                    if diffs:
                        total_errors = sum(d.get('errors', 0) for d in diffs)
                        return (total_errors / len(diffs)) * 100
                except (json.JSONDecodeError, TypeError):
                    # If the stored JSON is malformed or not the expected structure,
                    # treat it as having no recent diffs and fall back to 0.0 below.
                    pass
        
        return 0.0
    
    def check_degradation(self, agent_id: str, error_threshold: int = 20) -> Tuple[bool, str]:
        """
        Check if agent shows signs of degradation.
        Note: ERROR_THRESHOLD_PERCENT is a parameter to avoid circular import.
        """
        error_rate = self.get_error_rate(agent_id)
        
        if error_rate >= error_threshold:
            return True, f"Error rate {error_rate:.1f}% exceeds threshold ({error_threshold}%)"
        
        return False, f"Error rate: {error_rate:.1f}%"
    
    # ========== Phase 9: Break System ==========
    
    def record_break(self, agent_id: str, break_type: str, duration_minutes: int) -> None:
        """Record a break taken by an agent."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Get or initialize break history
            c.execute('SELECT memory_json FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row:
                try:
                    memory = json.loads(row[0]) if row[0] else {}
                except json.JSONDecodeError:
                    memory = {}
                
                # Initialize or update break history
                if 'breaks' not in memory:
                    memory['breaks'] = []
                
                memory['breaks'].append({
                    'type': break_type,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'duration_minutes': duration_minutes
                })
                
                # Keep only last 24 hours of breaks
                cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
                memory['breaks'] = [b for b in memory['breaks'] if b['timestamp'] > cutoff]
                
                c.execute('''
                    UPDATE agent_state SET memory_json = ?, last_updated = ?
                    WHERE agent_id = ?
                ''', (json.dumps(memory), datetime.now(timezone.utc), agent_id))
                conn.commit()
    
    def get_breaks_in_last_hour(self, agent_id: str) -> int:
        """Get number of breaks taken in the last hour."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT memory_json FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row and row[0]:
                try:
                    memory = json.loads(row[0])
                    breaks = memory.get('breaks', [])
                    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
                    return len([b for b in breaks if b['timestamp'] > cutoff])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return 0
    
    def can_take_break(self, agent_id: str, total_agents: int, agents_on_break: int,
                      max_breaks_per_hour: int = 2, max_workforce_on_break: float = 0.4) -> Tuple[bool, str]:
        """
        Check if an agent can take a break.
        Note: Constants are parameters to avoid circular import.
        """
        # Check maximum breaks per hour
        breaks_this_hour = self.get_breaks_in_last_hour(agent_id)
        if breaks_this_hour >= max_breaks_per_hour:
            return False, f"Maximum breaks per hour ({max_breaks_per_hour}) reached"
        
        # Check maximum workforce percentage on break
        if total_agents > 0:
            workforce_on_break = agents_on_break / total_agents
            if workforce_on_break >= max_workforce_on_break:
                return False, f"Too many agents on break ({agents_on_break}/{total_agents})"
        
        return True, "Break approved"
    
    # ========== Phase 8: Token Tracking ==========
    
    def update_token_usage(self, agent_id: str, tokens_used: int) -> None:
        """
        Update token usage for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            tokens_used: Total tokens used by the agent
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE agent_state SET tokens_used = ?, last_updated = ?
                WHERE agent_id = ?
            ''', (tokens_used, datetime.now(timezone.utc), agent_id))
            conn.commit()
    
    def get_token_usage(self, agent_id: str) -> int:
        """
        Get token usage for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Total tokens used, or 0 if agent not found
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT tokens_used FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            return row[0] if row and row[0] else 0
    
    def save_context_summary(self, agent_id: str, summary: str) -> None:
        """
        Save a compressed context summary for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            summary: Compressed context summary text
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE agent_state SET context_summary = ?, last_updated = ?
                WHERE agent_id = ?
            ''', (summary, datetime.now(timezone.utc), agent_id))
            conn.commit()
    
    def get_context_summary(self, agent_id: str) -> Optional[str]:
        """
        Get context summary for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            Context summary text, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT context_summary FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            return row[0] if row else None
    
    # ========== Phase 7: Persistence Lifecycle Hooks ==========
    
    def restore_all_agents(self) -> List[Dict[str, Any]]:
        """
        Restore all agents from database on startup.
        
        Returns:
            List of agent state dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT agent_id, alias, model_name, memory_json, xp, level, 
                       status, tokens_used, context_summary
                FROM agent_state
                WHERE status IN ('active', 'sleeping')
                ORDER BY xp DESC
            ''')
            rows = c.fetchall()
            
            agents = []
            for row in rows:
                agent = {
                    'agent_id': row[0],
                    'alias': row[1],
                    'model_name': row[2],
                    'memory': json.loads(row[3]) if row[3] else {},
                    'xp': row[4],
                    'level': row[5],
                    'status': row[6],
                    'tokens_used': row[7] if row[7] else 0,
                    'context_summary': row[8]
                }
                agents.append(agent)
            
            return agents
    
    def sync_conversation(self, agent_id: str, message_snippet: str, 
                         message_type: str = 'message') -> None:
        """
        Store conversation snippet in agent memory for context continuity.
        
        Args:
            agent_id: Unique identifier for the agent
            message_snippet: Short snippet of conversation to store
            message_type: Type of message ('message', 'action', 'thought', etc.)
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT memory_json FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row:
                try:
                    memory = json.loads(row[0]) if row[0] else {}
                except json.JSONDecodeError:
                    memory = {}
                
                # Initialize conversation history if not present
                if 'conversation_history' not in memory:
                    memory['conversation_history'] = []
                
                # Add new message snippet
                memory['conversation_history'].append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'type': message_type,
                    'content': message_snippet[:500]  # Limit snippet size
                })
                
                # Keep only last 50 messages
                memory['conversation_history'] = memory['conversation_history'][-50:]
                
                c.execute('''
                    UPDATE agent_state SET memory_json = ?, last_updated = ?
                    WHERE agent_id = ?
                ''', (json.dumps(memory), datetime.now(timezone.utc), agent_id))
                conn.commit()
    
    def get_agent_context_history(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            limit: Maximum number of messages to return
        
        Returns:
            List of conversation history entries
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT memory_json FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = c.fetchone()
            
            if row and row[0]:
                try:
                    memory = json.loads(row[0])
                    history = memory.get('conversation_history', [])
                    return history[-limit:] if history else []
                except (json.JSONDecodeError, TypeError):
                    return []
        
        return []
        
        # Check workforce on break percentage
        if total_agents > 0:
            on_break_ratio = (agents_on_break + 1) / total_agents
            if on_break_ratio > max_workforce_on_break:
                return False, f"Too many agents on break ({on_break_ratio:.0%} > {max_workforce_on_break:.0%})"
        
        return True, "Break approved"
