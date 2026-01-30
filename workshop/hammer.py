"""
Hammer - Live Instrumentation Tool
Provides runtime instrumentation and monitoring capabilities for dynamic analysis.
Uses Frida for hooking into running processes and monitoring execution.
"""
import frida
import time
import re
from typing import Dict, Any, Optional, Callable
import logging
import threading
logger = logging.getLogger(__name__)
def _sanitize_js_string(value: str) -> str:
    """
    Sanitize a string for safe embedding in JavaScript code.
    Escapes single quotes, double quotes, backslashes, and newlines
    to prevent JavaScript injection attacks.
    """
    if not isinstance(value, str):
        value = str(value)
    # Escape backslashes first, then quotes and newlines
    value = value.replace('\\', '\\\\')
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    return value
def _validate_identifier(name: str) -> bool:
    """
    Validate that a name is a safe identifier (alphanumeric, underscore, dash).
    Returns True if valid, False otherwise.
    """
    if not name or not isinstance(name, str):
        return False
    # Reject strings with newlines, carriage returns, or null bytes
    if '\n' in name or '\r' in name or '\0' in name:
        return False
    # Allow alphanumeric, underscore, dash, and dot (for namespaced functions)
    return bool(re.match(r'^[a-zA-Z0-9_\.\-]+$', name))
class HammerInstrumentor:
    """
    Live instrumentation tool for hammering in runtime hooks and monitoring.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sessions = {}
        self.hooks = {}
        self.monitoring = False
    def instrument_process(self, process_name: str, hooks: Dict[str, Any]) -> str:
        """
        Instrument a running process with the specified hooks.
        Args:
            process_name: Name of the process to instrument
            hooks: Dictionary of hooks to attach
        Returns:
            Session ID for the instrumentation session
        """
        try:
            # Find the process
            pid = self._find_process_pid(process_name)
            if not pid:
                return f"Process {process_name} not found"
            # Create Frida session
            session = frida.attach(pid)
            session_id = f"{process_name}_{pid}_{int(time.time())}"
            self.sessions[session_id] = session
            self.hooks[session_id] = {}
            # Attach hooks
            for hook_name, hook_config in hooks.items():
                self._attach_hook(session, session_id, hook_name, hook_config)
            logger.info(f"Instrumented process {process_name} (PID: {pid})")
            return session_id
        except Exception as e:
            logger.error(f"Failed to instrument {process_name}: {e}")
            return f"Instrumentation failed: {e}"
    def instrument_script(self, script_path: str, hooks: Dict[str, Any]) -> str:
        """
        Instrument a Python script execution.
        Args:
            script_path: Path to the Python script
            hooks: Hooks to attach
        Returns:
            Session ID
        """
        try:
            # Create Frida script for Python instrumentation
            script_code = self._generate_python_hook_script(hooks)
            # Spawn the process with instrumentation
            pid = frida.spawn([script_path])
            session = frida.attach(pid)
            session_id = f"script_{script_path}_{pid}_{int(time.time())}"
            self.sessions[session_id] = session
            # Create and load the script
            script = session.create_script(script_code)
            script.load()
            # Resume the process
            frida.resume(pid)
            self.hooks[session_id] = script
            logger.info(f"Instrumented script {script_path} (PID: {pid})")
            return session_id
        except Exception as e:
            logger.error(f"Failed to instrument script {script_path}: {e}")
            return f"Script instrumentation failed: {e}"
    def start_monitoring(self, session_id: str, callback: Optional[Callable] = None) -> bool:
        """
        Start monitoring an instrumented session.
        Args:
            session_id: Session to monitor
            callback: Optional callback for monitoring events
        Returns:
            True if monitoring started successfully
        """
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found")
            return False
        self.monitoring = True
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitor_session,
            args=(session_id, callback),
            daemon=True
        )
        monitor_thread.start()
        logger.info(f"Started monitoring session {session_id}")
        return True
    def stop_monitoring(self, session_id: str) -> bool:
        """
        Stop monitoring a session.
        Args:
            session_id: Session to stop monitoring
        Returns:
            True if stopped successfully
        """
        if session_id not in self.sessions:
            return False
        self.monitoring = False
        # Detach hooks and session
        if session_id in self.hooks:
            hook = self.hooks[session_id]
            if hasattr(hook, 'unload'):
                hook.unload()
        session = self.sessions[session_id]
        session.detach()
        # Clean up
        del self.hooks[session_id]
        del self.sessions[session_id]
        logger.info(f"Stopped monitoring session {session_id}")
        return True
    def _find_process_pid(self, process_name: str) -> Optional[int]:
        """Find PID of a process by name."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == process_name:
                    return proc.info['pid']
        except ImportError:
            logger.warning("psutil not available for process discovery")
        except Exception as e:
            logger.error(f"Process discovery failed: {e}")
        return None
    def _attach_hook(self, session, session_id: str, hook_name: str, hook_config: Dict[str, Any]):
        """Attach a specific hook to the session."""
        hook_type = hook_config.get('type', 'function')
        if hook_type == 'function':
            self._attach_function_hook(session, session_id, hook_name, hook_config)
        elif hook_type == 'memory':
            self._attach_memory_hook(session, session_id, hook_name, hook_config)
        elif hook_type == 'syscall':
            self._attach_syscall_hook(session, session_id, hook_name, hook_config)
    def _attach_function_hook(self, session, session_id: str, hook_name: str, config: Dict[str, Any]):
        """Attach a function hook."""
        func_addr = config.get('address')
        if not func_addr:
            return
        # Validate and sanitize inputs
        if not _validate_identifier(hook_name):
            logger.error(f"Invalid hook name: {hook_name}")
            return
        # Sanitize for JavaScript embedding
        safe_hook_name = _sanitize_js_string(hook_name)
        safe_func_addr = _sanitize_js_string(str(func_addr))
        script_code = f"""
        Interceptor.attach(ptr('{safe_func_addr}'), {{
            onEnter: function(args) {{
                console.log('[Hammer] Entering {safe_hook_name}');
                // Log arguments
                for (var i = 0; i < args.length; i++) {{
                    console.log('  arg' + i + ': ' + args[i]);
                }}
            }},
            onLeave: function(retval) {{
                console.log('[Hammer] Leaving {safe_hook_name}, retval: ' + retval);
            }}
        }});
        """
        script = session.create_script(script_code)
        script.load()
        self.hooks[session_id][hook_name] = script
    def _attach_memory_hook(self, session, session_id: str, hook_name: str, config: Dict[str, Any]):
        """Attach a memory access hook."""
        addr = config.get('address')
        size = config.get('size', 4)
        script_code = f"""
        MemoryAccessMonitor.enable({{
            base: ptr('{addr}'),
            size: {size}
        }}, {{
            onAccess: function(details) {{
                console.log('[Hammer] Memory access at {addr}: ' + details.operation);
            }}
        }});
        """
        script = session.create_script(script_code)
        script.load()
        self.hooks[session_id][hook_name] = script
    def _attach_syscall_hook(self, session, session_id: str, hook_name: str, config: Dict[str, Any]):
        """Attach a syscall hook."""
        syscall_name = config.get('syscall')
        if not syscall_name:
            return
        # Validate and sanitize inputs
        if not _validate_identifier(syscall_name):
            logger.error(f"Invalid syscall name: {syscall_name}")
            return
        safe_syscall_name = _sanitize_js_string(syscall_name)
        script_code = f"""
        var syscall = Module.findExportByName(null, '{safe_syscall_name}');
        if (syscall) {{
            Interceptor.attach(syscall, {{
                onEnter: function(args) {{
                    console.log('[Hammer] Syscall {safe_syscall_name}');
                }}
            }});
        }}
        """
        script = session.create_script(script_code)
        script.load()
        self.hooks[session_id][hook_name] = script
    def _generate_python_hook_script(self, hooks: Dict[str, Any]) -> str:
        """Generate Frida script for Python instrumentation."""
        script_parts = []
        for hook_name, config in hooks.items():
            if config.get('type') == 'function':
                func_name = config.get('function')
                if not func_name:
                    continue
                # Validate and sanitize function name
                if not _validate_identifier(func_name):
                    logger.error(f"Invalid function name: {func_name}")
                    continue
                safe_func_name = _sanitize_js_string(func_name)
                script_parts.append(f"""
                // Hook Python function {safe_func_name}
                var func = Module.findExportByName(null, '{safe_func_name}');
                if (func) {{
                    Interceptor.attach(func, {{
                        onEnter: function(args) {{
                            console.log('[Hammer] Python call: {safe_func_name}');
                        }}
                    }});
                }}
                """)
        return "\n".join(script_parts)
    def _monitor_session(self, session_id: str, callback: Optional[Callable]):
        """Monitor a session for events."""
        while self.monitoring and session_id in self.sessions:
            try:
                # Check for messages from hooks
                if session_id in self.hooks:
                    hook = self.hooks[session_id]
                    if hasattr(hook, 'post'):
                        # Process any pending messages
                        pass
                time.sleep(0.1)  # Polling interval
            except Exception as e:
                logger.error(f"Monitoring error for {session_id}: {e}")
                break
        if callback:
            callback(session_id, "monitoring_stopped")