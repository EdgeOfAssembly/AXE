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


def process_agent_response(response: str, workspace: str, 
                          response_processor: Any) -> Tuple[str, List[str]]:
    """
    Main entry point for processing agent responses with XML function calls.
    
    Parses XML function calls, executes them, and returns formatted results.
    
    Args:
        response: Agent response that may contain XML function calls
        workspace: Workspace directory path
        response_processor: ResponseProcessor instance for tool execution
    
    Returns:
        Tuple of (original_response, list_of_xml_results)
    """
    # Parse XML function calls
    calls = parse_xml_function_calls(response)
    
    if not calls:
        # No XML function calls found
        return response, []
    
    # Execute each call and collect results
    xml_results = []
    
    for call in calls:
        result = execute_parsed_call(call, workspace, response_processor)
        
        # Format result in XML
        xml_result = format_xml_result(call['tool'], call['params'], result)
        xml_results.append(xml_result)
    
    return response, xml_results
