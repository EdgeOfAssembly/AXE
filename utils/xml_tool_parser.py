#!/usr/bin/env python3
"""
XML Function Call Parser for AXE

Parses native XML function call format used by LLM agents (Claude, GPT, Llama, Grok)
and converts them to AXE's internal tool execution format.

Example XML format:
    <function_calls>
    <invoke name="read_file">
    <parameter name="file_path">/tmp/playground/MISSION.md</parameter>
    </invoke>
    </function_calls>

Maps to AXE tools: READ, WRITE, APPEND, EXEC
"""
import re
import os
import json
from typing import List, Dict, Any, Tuple, Optional
import xml.etree.ElementTree as ET


# Tool name normalization mapping
TOOL_NAME_MAPPING = {
    # Read operations
    'read_file': 'READ',
    'read': 'READ',
    'cat': 'READ',
    'get_file': 'READ',
    'view_file': 'READ',
    
    # Write operations
    'write_file': 'WRITE',
    'write': 'WRITE',
    'create_file': 'WRITE',
    'save_file': 'WRITE',
    
    # Append operations
    'append_file': 'APPEND',
    'append_to_file': 'APPEND',
    'append': 'APPEND',
    
    # List directory operations
    'list_dir': 'EXEC',
    'list_directory': 'EXEC',
    'ls': 'EXEC',
    'listdir': 'EXEC',
    
    # Shell/exec operations
    'shell': 'EXEC',
    'run_shell': 'EXEC',
    'exec': 'EXEC',
    'bash': 'EXEC',
    'execute': 'EXEC',
    'run_command': 'EXEC',
}


def normalize_tool_name(name: str) -> Optional[str]:
    """
    Normalize tool name to AXE's internal format.
    
    Args:
        name: Original tool name from XML
    
    Returns:
        Normalized tool name (READ, WRITE, APPEND, EXEC) or None if unknown
    """
    name_lower = name.lower().strip()
    return TOOL_NAME_MAPPING.get(name_lower)


def parse_xml_function_calls(response: str) -> List[Dict[str, Any]]:
    """
    Parse XML function calls from agent response.
    
    Looks for <function_calls> blocks and extracts tool calls with parameters.
    
    Args:
        response: Agent response text that may contain XML function calls
    
    Returns:
        List of parsed function calls, each as a dict with:
        {
            'tool': 'READ'|'WRITE'|'APPEND'|'EXEC',
            'params': dict of parameter name -> value,
            'raw_name': original tool name from XML
        }
    """
    calls = []
    
    # Find all <function_calls> blocks
    # Pattern to extract function_calls blocks including nested content
    function_calls_pattern = r'<function_calls>(.*?)</function_calls>'
    
    matches = re.finditer(function_calls_pattern, response, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        block_content = match.group(1)
        
        # Parse each <invoke> within the function_calls block
        invoke_pattern = r'<invoke\s+name=["\']([^"\']+)["\']>(.*?)</invoke>'
        
        for invoke_match in re.finditer(invoke_pattern, block_content, re.DOTALL | re.IGNORECASE):
            tool_name = invoke_match.group(1)
            invoke_content = invoke_match.group(2)
            
            # Extract parameters
            params = {}
            param_pattern = r'<parameter\s+name=["\']([^"\']+)["\']>(.*?)</parameter>'
            
            for param_match in re.finditer(param_pattern, invoke_content, re.DOTALL | re.IGNORECASE):
                param_name = param_match.group(1)
                param_value = param_match.group(2).strip()
                params[param_name] = param_value
            
            # Normalize tool name
            normalized_tool = normalize_tool_name(tool_name)
            
            if normalized_tool:
                calls.append({
                    'tool': normalized_tool,
                    'params': params,
                    'raw_name': tool_name
                })
    
    return calls


def parse_bash_tags(response: str) -> List[Dict[str, Any]]:
    """
    Parse <bash>command</bash> format.
    
    Args:
        response: Agent response text
    
    Returns:
        List of parsed calls in standard format
    """
    pattern = r'<bash>(.*?)</bash>'
    calls = []
    for match in re.findall(pattern, response, re.DOTALL):
        cmd = match.strip()
        if cmd:
            calls.append({
                'tool': 'EXEC',
                'params': {'command': cmd},
                'raw_name': 'bash'
            })
    return calls


def parse_shell_codeblocks(response: str) -> List[Dict[str, Any]]:
    """
    Parse ```bash, ```shell, ```sh code blocks.
    
    Args:
        response: Agent response text
    
    Returns:
        List of parsed calls in standard format
    """
    # Match ```bash or ```shell or ```sh followed by content and closing ```
    # Make newline optional to handle inline code blocks
    pattern = r'```(?:bash|shell|sh)\n?(.*?)```'
    calls = []
    for match in re.findall(pattern, response, re.DOTALL):
        cmd = match.strip()
        if cmd:
            # Handle multi-line commands (execute each line)
            for line in cmd.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    calls.append({
                        'tool': 'EXEC',
                        'params': {'command': line},
                        'raw_name': 'shell'
                    })
    return calls


def parse_axe_native_blocks(response: str) -> List[Dict[str, Any]]:
    """
    Parse AXE native ```READ, ```WRITE, ```EXEC blocks.
    
    Args:
        response: Agent response text
    
    Returns:
        List of parsed calls in standard format
    """
    calls = []
    
    # ```READ /path``` - Use non-greedy match and stop at closing backticks
    read_pattern = r'```READ\s+([^`]+?)```'
    for path in re.findall(read_pattern, response):
        calls.append({
            'tool': 'READ',
            'params': {'file_path': path.strip()},
            'raw_name': 'READ'
        })
    
    # ```EXEC command``` - Use non-greedy match for command
    exec_pattern = r'```EXEC\s+([^`]+?)```'
    for cmd in re.findall(exec_pattern, response):
        calls.append({
            'tool': 'EXEC',
            'params': {'command': cmd.strip()},
            'raw_name': 'EXEC'
        })
    
    # ```WRITE /path\ncontent``` - Make content optional
    write_pattern = r'```WRITE\s+([^\n`]+)(?:\n(.*?))?```'
    for match in re.findall(write_pattern, response, re.DOTALL):
        path = match[0]
        content = match[1] if len(match) > 1 and match[1] else ''
        calls.append({
            'tool': 'WRITE',
            'params': {'file_path': path.strip(), 'content': content},
            'raw_name': 'WRITE'
        })
    
    return calls


def parse_simple_xml_tags(response: str) -> List[Dict[str, Any]]:
    """
    Parse simple XML tags like <read_file>, <shell>, <bash>.
    
    Args:
        response: Agent response text
    
    Returns:
        List of parsed calls in standard format
    """
    calls = []
    
    # <read_file>/path</read_file>
    for path in re.findall(r'<read_file>(.*?)</read_file>', response, re.DOTALL):
        calls.append({
            'tool': 'READ',
            'params': {'file_path': path.strip()},
            'raw_name': 'read_file'
        })
    
    # <shell>command</shell>
    for cmd in re.findall(r'<shell>(.*?)</shell>', response, re.DOTALL):
        calls.append({
            'tool': 'EXEC',
            'params': {'command': cmd.strip()},
            'raw_name': 'shell'
        })
    
    # <write_file path="...">content</write_file>
    for match in re.findall(r'<write_file\s+path=["\']([^"\']+)["\']>(.*?)</write_file>', response, re.DOTALL):
        path, content = match
        calls.append({
            'tool': 'WRITE',
            'params': {'file_path': path.strip(), 'content': content},
            'raw_name': 'write_file'
        })
    
    return calls


def deduplicate_calls(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate tool calls.
    
    Args:
        calls: List of parsed calls
    
    Returns:
        Deduplicated list of calls
    """
    seen = set()
    unique = []
    for call in calls:
        # Use JSON serialization for consistent hashing
        key = (call['tool'], json.dumps(call['params'], sort_keys=True))
        if key not in seen:
            seen.add(key)
            unique.append(call)
    return unique


def parse_all_tool_formats(response: str) -> List[Dict[str, Any]]:
    """
    Parse ALL known LLM tool-calling formats from agent response.
    Returns unified list of tool calls.
    
    Args:
        response: Agent response text that may contain various tool call formats
    
    Returns:
        List of parsed calls from all formats, deduplicated
    """
    calls = []
    
    # 1. XML function_calls format (existing from PR #6)
    calls.extend(parse_xml_function_calls(response))
    
    # 2. <bash> format
    calls.extend(parse_bash_tags(response))
    
    # 3. ```bash / ```shell / ```sh code blocks
    calls.extend(parse_shell_codeblocks(response))
    
    # 4. AXE native ```READ/WRITE/EXEC``` blocks
    calls.extend(parse_axe_native_blocks(response))
    
    # 5. Simple XML tags like <read_file>, <shell>
    calls.extend(parse_simple_xml_tags(response))
    
    # Deduplicate identical calls
    return deduplicate_calls(calls)


def execute_parsed_call(call: Dict[str, Any], workspace: str, 
                       response_processor: Any) -> str:
    """
    Execute a parsed function call using AXE's tools.
    
    Args:
        call: Parsed function call dict with 'tool', 'params', 'raw_name'
        workspace: Workspace directory path
        response_processor: ResponseProcessor instance with _handle_read, _handle_write, etc.
    
    Returns:
        Result string from tool execution
    """
    tool = call['tool']
    params = call['params']
    
    try:
        if tool == 'READ':
            # Extract file path from various parameter names
            filepath = (params.get('file_path') or 
                       params.get('path') or 
                       params.get('filename') or 
                       params.get('file'))
            
            if not filepath:
                return "ERROR: No file path provided for READ operation"
            
            return response_processor._handle_read(filepath)
        
        elif tool == 'WRITE':
            # Extract file path and content
            filepath = (params.get('file_path') or 
                       params.get('path') or 
                       params.get('filename') or 
                       params.get('file'))
            
            content = (params.get('content') or 
                      params.get('data') or 
                      params.get('text') or 
                      params.get('contents') or 
                      '')
            
            if not filepath:
                return "ERROR: No file path provided for WRITE operation"
            
            return response_processor._handle_write(filepath, content)
        
        elif tool == 'APPEND':
            # Extract file path and content
            filepath = (params.get('file_path') or 
                       params.get('path') or 
                       params.get('filename') or 
                       params.get('file'))
            
            content = (params.get('content') or 
                      params.get('data') or 
                      params.get('text') or 
                      params.get('contents') or 
                      '')
            
            if not filepath:
                return "ERROR: No file path provided for APPEND operation"
            
            # Implement append by reading, then writing
            try:
                existing_content = ""
                filepath_resolved = response_processor._resolve_project_path(filepath)
                if filepath_resolved and os.path.exists(filepath_resolved):
                    with open(filepath_resolved, 'r', encoding='utf-8', errors='replace') as f:
                        existing_content = f.read()
                
                new_content = existing_content + content
                return response_processor._handle_write(filepath, new_content)
            except Exception as e:
                return f"ERROR during APPEND: {e}"
        
        elif tool == 'EXEC':
            # For list_dir operations, convert to ls command
            if call['raw_name'].lower() in ['list_dir', 'list_directory', 'ls', 'listdir']:
                dirpath = (params.get('path') or 
                          params.get('directory') or 
                          params.get('dir') or 
                          '.')
                command = f"ls -la {dirpath}"
            else:
                # Regular shell command
                command = (params.get('command') or 
                          params.get('cmd') or 
                          params.get('shell_command') or 
                          '')
            
            if not command:
                return "ERROR: No command provided for EXEC operation"
            
            return response_processor._handle_exec(command)
        
        else:
            return f"ERROR: Unknown tool type '{tool}'"
    
    except Exception as e:
        return f"ERROR executing {tool}: {e}"


def format_xml_result(tool: str, params: Dict[str, Any], result: str) -> str:
    """
    Format execution result in XML format that agents expect.
    
    Args:
        tool: Tool name (READ, WRITE, EXEC, APPEND)
        params: Parameters used for the call
        result: Execution result string
    
    Returns:
        XML-formatted result string
    """
    # Escape XML special characters in result
    result_escaped = result.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    return f"""<result>
<function_result>
<result>
{result_escaped}
</result>
</function_result>
</result>"""


def clean_tool_syntax(response: str) -> str:
    """
    Remove all tool-calling syntax from response for cleaner display.
    
    Args:
        response: Agent response with tool syntax
    
    Returns:
        Cleaned response with tool calls replaced
    """
    cleaned = response
    
    # Remove <function_calls>...</function_calls>
    cleaned = re.sub(r'<function_calls>.*?</function_calls>', '[TOOL EXECUTED]', cleaned, flags=re.DOTALL)
    
    # Remove <bash>...</bash>
    cleaned = re.sub(r'<bash>.*?</bash>', '[TOOL EXECUTED]', cleaned, flags=re.DOTALL)
    
    # Remove ```bash...``` blocks - make newline optional to match parser logic
    cleaned = re.sub(r'```(?:bash|shell|sh)\n?.*?```', '[TOOL EXECUTED]', cleaned, flags=re.DOTALL)
    
    # Remove ```READ/WRITE/EXEC...``` blocks
    cleaned = re.sub(r'```(?:READ|WRITE|EXEC).*?```', '[TOOL EXECUTED]', cleaned, flags=re.DOTALL)
    
    return cleaned


def process_agent_response(response: str, workspace: str, 
                          response_processor: Any) -> Tuple[str, List[str]]:
    """
    Main entry point for processing agent responses with ALL tool call formats.
    
    Parses all known tool call formats, executes them, and returns formatted results.
    
    Args:
        response: Agent response that may contain various tool call formats
        workspace: Workspace directory path
        response_processor: ResponseProcessor instance for tool execution
    
    Returns:
        Tuple of (original_response, list_of_xml_results)
    """
    # Use comprehensive parser instead of just XML
    calls = parse_all_tool_formats(response)
    
    if not calls:
        # No tool calls found
        return response, []
    
    # Execute each call and collect results
    xml_results = []
    
    for call in calls:
        result = execute_parsed_call(call, workspace, response_processor)
        
        # Format result in XML
        xml_result = format_xml_result(call['tool'], call['params'], result)
        xml_results.append(xml_result)
    
    return response, xml_results
