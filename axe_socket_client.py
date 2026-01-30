#!/usr/bin/env python3
"""
Simple client for testing AXE's Unix socket interface.

Usage:
    python3 axe_socket_client.py "command to send"
    
Example:
    python3 axe_socket_client.py "/help"
    python3 axe_socket_client.py "@claude analyze main.c"
"""
import os
import sys
import socket


def send_command(command: str) -> str:
    """
    Send a command to AXE via Unix socket and return the response.
    
    Args:
        command: Command to send (slash command or agent message)
        
    Returns:
        Response from AXE including ANSI colors
        
    Raises:
        FileNotFoundError: If socket file doesn't exist
        ConnectionRefusedError: If can't connect to socket
    """
    uid = os.getuid()
    sock_path = f"/run/user/{uid}/axe.sock"
    pid_path = f"/run/user/{uid}/axe.pid"
    
    # Check if AXE is running
    if not os.path.exists(pid_path):
        raise FileNotFoundError(
            f"AXE is not running (PID file not found: {pid_path})\n"
            f"Start AXE in interactive mode: python3 axe.py"
        )
    
    # Read PID
    with open(pid_path) as f:
        axe_pid = f.read().strip()
    
    print(f"Connecting to AXE (PID {axe_pid})...", file=sys.stderr)
    
    # Check if socket exists
    if not os.path.exists(sock_path):
        raise FileNotFoundError(
            f"Socket file not found: {sock_path}\n"
            f"AXE may not be in interactive mode"
        )
    
    # Connect to socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(30)  # 30 second timeout
    
    try:
        s.connect(sock_path)
        print(f"Connected to {sock_path}", file=sys.stderr)
        
        # Send command (add newline if not present)
        if not command.endswith('\n'):
            command += '\n'
        
        s.sendall(command.encode('utf-8'))
        print(f"Sent: {command.strip()}", file=sys.stderr)
        
        # Receive response
        response = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
            # If we got a complete response, break
            # (This is a simple heuristic - in practice you might want
            # a better end-of-message detection)
            if len(chunk) < 4096:
                break
        
        return response.decode('utf-8')
        
    finally:
        s.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 axe_socket_client.py <command>", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  python3 axe_socket_client.py '/help'", file=sys.stderr)
        print("  python3 axe_socket_client.py '/agents'", file=sys.stderr)
        print("  python3 axe_socket_client.py '@claude analyze this'", file=sys.stderr)
        sys.exit(1)
    
    command = ' '.join(sys.argv[1:])
    
    try:
        response = send_command(command)
        print("\n" + "=" * 70, file=sys.stderr)
        print("RESPONSE FROM AXE:", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(response)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError as e:
        print(f"Error: Connection refused - {e}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print("Error: Timeout waiting for response", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
