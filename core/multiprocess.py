"""
Multiprocessing architecture for parallel agent thinking.

This module implements a system where each agent has its own private process
for background thinking. While one agent responds, others can prepare responses,
analyze context, and plan ahead.

Architecture:
- AgentWorkerProcess: Individual agent background process
- SharedContext: Thread-safe shared state between agents
- MultiAgentCoordinator: Orchestrates all agent processes
"""

import logging
from multiprocessing import Process, Queue, Manager, Event
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timezone
from queue import Empty


class SharedContext:
    """
    Thread-safe shared state between agents.
    
    Uses multiprocessing.Manager to provide shared data structures
    that can be accessed safely from multiple processes.
    """
    
    def __init__(self):
        """Initialize shared context with Manager."""
        self.manager = Manager()
        
        # Shared data structures
        self.conversation_history = self.manager.list()  # List of message dicts
        self.workspace_state = self.manager.dict()  # Current workspace state
        self.agent_status = self.manager.dict()  # Maps agent_id to status
        self.shared_notes = self.manager.dict()  # Shared notes/findings
        
        # Control flags
        self.shutdown_flag = self.manager.Event()
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to shared conversation history.
        
        Args:
            message: Message dictionary with keys like 'agent', 'content', 'timestamp'
        """
        self.conversation_history.append(message)
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent messages from conversation history.
        
        Args:
            limit: Maximum number of messages to return
        
        Returns:
            List of recent message dictionaries
        """
        return list(self.conversation_history[-limit:])
    
    def update_workspace(self, key: str, value: Any) -> None:
        """
        Update workspace state.
        
        Args:
            key: State key
            value: State value
        """
        self.workspace_state[key] = value
    
    def get_workspace_state(self) -> Dict[str, Any]:
        """
        Get current workspace state.
        
        Returns:
            Dictionary of workspace state
        """
        return dict(self.workspace_state)
    
    def update_agent_status(self, agent_id: str, status: str) -> None:
        """
        Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: Status string ('thinking', 'responding', 'idle', 'waiting')
        """
        self.agent_status[agent_id] = {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent status.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Status dictionary or None if agent not found
        """
        return self.agent_status.get(agent_id)
    
    def add_shared_note(self, key: str, note: str) -> None:
        """
        Add a shared note/finding.
        
        Args:
            key: Note identifier
            note: Note content
        """
        self.shared_notes[key] = {
            'content': note,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_shared_notes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all shared notes.
        
        Returns:
            Dictionary of shared notes
        """
        return dict(self.shared_notes)
    
    def request_shutdown(self) -> None:
        """Signal all processes to shut down."""
        self.shutdown_flag.set()
    
    def should_shutdown(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_flag.is_set()
    
    def cleanup(self) -> None:
        """Clean up Manager resources."""
        try:
            self.manager.shutdown()
        except Exception:
            # Manager may already be shut down
            pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        return False


class AgentWorkerProcess:
    """
    Individual agent background process.
    
    Each agent runs in its own process, continuously:
    1. Monitoring shared context updates
    2. Preparing potential responses
    3. Analyzing the current situation
    4. Waiting for its turn to respond
    """
    
    def __init__(self, agent_id: str, agent_name: str, 
                 input_queue: Queue, output_queue: Queue,
                 shared_context: SharedContext):
        """
        Initialize agent worker process.
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Agent name (e.g., 'claude', 'gpt')
            input_queue: Queue for receiving commands
            output_queue: Queue for sending responses
            shared_context: Shared context object
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.shared_context = shared_context
        self.running = False
        
        # Background thinking state - use Queue for thread-safe operations
        self.thoughts_queue = Queue()
        self.prepared_response = None
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Continuously monitors for:
        - Commands from coordinator (your turn, update context, shutdown)
        - Context updates to think about
        """
        self.running = True
        self.shared_context.update_agent_status(self.agent_id, 'starting')
        
        while self.running and not self.shared_context.should_shutdown():
            try:
                # Check for commands with short timeout
                try:
                    command = self.input_queue.get(timeout=0.5)
                    self.handle_command(command)
                except Empty:
                    # No command, continue background thinking
                    self.background_think()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Worker {self.agent_name} error: {e}", exc_info=True)
                time.sleep(1)
        
        self.shared_context.update_agent_status(self.agent_id, 'stopped')
    
    def handle_command(self, command: Dict[str, Any]) -> None:
        """
        Handle a command from the coordinator.
        
        Args:
            command: Command dictionary with 'type' and other fields
        """
        cmd_type = command.get('type')
        
        if cmd_type == 'your_turn':
            # It's our turn to respond
            self.handle_turn(command)
        
        elif cmd_type == 'context_update':
            # New information added to context
            self.handle_context_update(command)
        
        elif cmd_type == 'shutdown':
            # Time to shut down
            self.running = False
        
        elif cmd_type == 'ping':
            # Health check
            self.output_queue.put({
                'type': 'pong',
                'agent_id': self.agent_id
            })
    
    def handle_turn(self, command: Dict[str, Any]) -> None:
        """
        Handle when it's this agent's turn to respond.
        
        Args:
            command: Turn command with prompt and context
        """
        self.shared_context.update_agent_status(self.agent_id, 'responding')
        
        # Collect all thoughts from the queue
        thoughts = []
        while not self.thoughts_queue.empty():
            try:
                thoughts.append(self.thoughts_queue.get_nowait())
            except Empty:
                break
        
        # Send prepared thoughts and response
        response = {
            'type': 'response',
            'agent_id': self.agent_id,
            'thoughts': thoughts,
            'prepared_response': self.prepared_response,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.output_queue.put(response)
        
        # Clear prepared state
        self.prepared_response = None
        
        self.shared_context.update_agent_status(self.agent_id, 'idle')
    
    def handle_context_update(self, command: Dict[str, Any]) -> None:
        """
        Handle context update notification.
        
        Args:
            command: Context update command
        """
        # In a real implementation, this would trigger analysis
        # For now, just note that we received it
        update_type = command.get('update_type', 'unknown')
        self.thoughts_queue.put(f"Noted: {update_type} update")
    
    def background_think(self) -> None:
        """
        Perform background thinking while waiting.
        
        This is called continuously when no commands are pending.
        The agent can:
        - Analyze recent messages
        - Prepare potential responses
        - Plan ahead
        """
        self.shared_context.update_agent_status(self.agent_id, 'thinking')
        
        # Get recent context
        recent_messages = self.shared_context.get_recent_messages(limit=5)
        
        # In a real implementation, this would do actual analysis
        # For now, just simulate thinking
        if recent_messages and not self.prepared_response:
            self.prepared_response = f"[{self.agent_name} has been thinking about the recent {len(recent_messages)} messages]"
        
        # Brief sleep to avoid busy-waiting
        time.sleep(0.1)


class MultiAgentCoordinator:
    """
    Orchestrates all agent processes.
    
    Responsibilities:
    - Spawn worker processes for each agent
    - Broadcast context updates to all agents
    - Signal agents when it's their turn
    - Collect prepared responses
    - Handle graceful shutdown
    """
    
    def __init__(self, agent_configs: List[Dict[str, str]]):
        """
        Initialize coordinator.
        
        Args:
            agent_configs: List of agent configuration dicts with 'agent_id' and 'name'
        """
        self.agent_configs = agent_configs
        self.shared_context = SharedContext()
        
        # Process management
        self.workers = {}  # Maps agent_id to worker info
        self.processes = {}  # Maps agent_id to Process object
        
        # Communication queues
        self.input_queues = {}  # Maps agent_id to input queue
        self.output_queues = {}  # Maps agent_id to output queue
    
    def start(self) -> None:
        """Start all agent worker processes."""
        for config in self.agent_configs:
            agent_id = config['agent_id']
            agent_name = config['name']
            
            # Create communication queues
            input_queue = Queue()
            output_queue = Queue()
            
            self.input_queues[agent_id] = input_queue
            self.output_queues[agent_id] = output_queue
            
            # Create worker
            worker = AgentWorkerProcess(
                agent_id=agent_id,
                agent_name=agent_name,
                input_queue=input_queue,
                output_queue=output_queue,
                shared_context=self.shared_context
            )
            
            # Start process
            process = Process(target=worker.run)
            process.start()
            
            self.workers[agent_id] = {
                'name': agent_name,
                'worker': worker,
                'input_queue': input_queue,
                'output_queue': output_queue
            }
            self.processes[agent_id] = process
        
        # Wait briefly for workers to start
        time.sleep(0.5)
    
    def broadcast_context_update(self, update_type: str, data: Any = None) -> None:
        """
        Broadcast a context update to all agents.
        
        Args:
            update_type: Type of update
            data: Optional update data
        """
        command = {
            'type': 'context_update',
            'update_type': update_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        for agent_id, worker_info in self.workers.items():
            worker_info['input_queue'].put(command)
    
    def signal_turn(self, agent_id: str, prompt: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        Signal an agent that it's their turn to respond.
        
        Args:
            agent_id: Agent to signal
            prompt: The prompt/question
            context: Additional context
        
        Returns:
            Agent's response dictionary or None if timeout
        """
        if agent_id not in self.workers:
            return None
        
        command = {
            'type': 'your_turn',
            'prompt': prompt,
            'context': context,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.workers[agent_id]['input_queue'].put(command)
        
        # Wait for response (with timeout)
        try:
            response = self.workers[agent_id]['output_queue'].get(timeout=30)
            return response
        except Empty:
            return None
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all agents.
        
        Returns:
            Dictionary mapping agent_id to status info
        """
        status = {}
        for agent_id in self.workers.keys():
            agent_status = self.shared_context.get_agent_status(agent_id)
            status[agent_id] = agent_status if agent_status else {'status': 'unknown'}
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown all worker processes gracefully."""
        # Signal shutdown
        self.shared_context.request_shutdown()
        
        # Send shutdown command to all workers
        for agent_id, worker_info in self.workers.items():
            worker_info['input_queue'].put({'type': 'shutdown'})
        
        # Wait for processes to finish (with timeout)
        for agent_id, process in self.processes.items():
            process.join(timeout=5)
            if process.is_alive():
                # Force terminate if still running
                process.terminate()
                process.join(timeout=2)
        
        # Clean up
        self.processes.clear()
        self.workers.clear()
