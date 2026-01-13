"""
Session persistence and management for AXE.
Allows saving/loading/listing conversation sessions.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class SessionManager:
    """Manages session save/load/list operations."""
    
    def __init__(self, sessions_dir: str = ".axe_sessions"):
        """
        Initialize session manager.
        
        Args:
            sessions_dir: Directory to store session files (default: .axe_sessions)
        """
        self.sessions_dir = os.path.abspath(sessions_dir)
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def save_session(self, session_name: str, session_data: Dict[str, Any]) -> bool:
        """
        Save a session to a JSON file.
        
        Args:
            session_name: Name of the session
            session_data: Dictionary containing:
                - conversation: List of conversation history
                - workspace: Current workspace path
                - agents: List of active agent names
                - metadata: Additional metadata (tokens_used, duration, etc.)
                - file_ids: Optional dict of file IDs from Files API (Anthropic)
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Add timestamp to session data
            session_data['timestamp'] = datetime.now().isoformat()
            session_data['session_id'] = session_name
            
            # Create filename-safe session name
            safe_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_'))
            
            # Warn if sanitized name differs from input
            if safe_name != session_name:
                print(f"Note: Session name '{session_name}' sanitized to '{safe_name}' for filesystem compatibility")
            
            filepath = os.path.join(self.sessions_dir, f"{safe_name}.json")
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return True
        except Exception as e:
            import traceback
            print(f"Error saving session: {e}")
            traceback.print_exc()
            return False
    
    def load_session(self, session_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a session from a JSON file.
        
        Args:
            session_name: Name of the session to load
        
        Returns:
            Dictionary with session data, or None if not found/error
        """
        try:
            # Create filename-safe session name
            safe_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_'))
            filepath = os.path.join(self.sessions_dir, f"{safe_name}.json")
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            import traceback
            print(f"Error loading session: {e}")
            traceback.print_exc()
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available saved sessions.
        
        Returns:
            List of dictionaries with session info:
                - name: Session name
                - timestamp: When session was saved
                - workspace: Workspace path
                - agents: List of agents
                - size: File size in bytes
        """
        sessions = []
        
        try:
            for filename in os.listdir(self.sessions_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.sessions_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        'name': data.get('session_id', filename.replace('.json', '')),
                        'timestamp': data.get('timestamp', 'Unknown'),
                        'workspace': data.get('workspace', 'Unknown'),
                        'agents': data.get('agents', []),
                        'size': os.path.getsize(filepath),
                        'filepath': filepath
                    })
                except Exception as e:
                    # Skip corrupted session files, but warn the user about the issue
                    print(f"Warning: Skipping corrupted or unreadable session file '{filepath}': {e}")
                    continue
            
            # Sort by timestamp (newest first)
            sessions.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            print(f"Error listing sessions: {e}")
        
        return sessions
    
    def delete_session(self, session_name: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_name: Name of the session to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            safe_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_'))
            filepath = os.path.join(self.sessions_dir, f"{safe_name}.json")
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
