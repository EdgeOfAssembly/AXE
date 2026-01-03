"""
Saw - Taint Analysis Tool

Tracks data flow through code to identify tainted inputs and potential vulnerabilities.
Combines static and dynamic analysis for comprehensive taint tracking.
"""

import ast
import inspect
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TaintSource:
    """Represents a source of tainted data."""
    name: str
    location: str  # e.g., "function.parameter" or "global.variable"
    type_hint: Optional[str] = None

@dataclass
class TaintSink:
    """Represents a sink where tainted data could cause issues."""
    name: str
    location: str
    vulnerability_type: str  # e.g., "sql_injection", "xss", "command_injection"

@dataclass
class TaintFlow:
    """Represents a flow of tainted data from source to sink."""
    source: TaintSource
    sink: TaintSink
    path: List[str]  # List of variable/function names in the flow
    confidence: float  # 0.0 to 1.0

class SawTracker:
    """
    Taint analysis tracker for cutting through data flows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sources = self._load_default_sources()
        self.sinks = self._load_default_sinks()
        self.taint_graph = {}  # variable -> set of taint sources

    def analyze_code(self, code: str, filename: str = "<string>") -> Dict[str, Any]:
        """
        Analyze Python code for taint flows.

        Args:
            code: Python source code to analyze
            filename: Filename for error reporting

        Returns:
            Dict containing taint flows, sources, and sinks found
        """
        try:
            tree = ast.parse(code, filename=filename)
            analyzer = TaintAnalyzer(self.sources, self.sinks)
            analyzer.visit(tree)

            results = {
                'sources_found': [s.__dict__ for s in analyzer.sources_found],
                'sinks_found': [s.__dict__ for s in analyzer.sinks_found],
                'taint_flows': [f.__dict__ for f in analyzer.flows],
                'vulnerabilities': self._classify_vulnerabilities(analyzer.flows)
            }

            return results

        except SyntaxError as e:
            logger.error(f"Syntax error in {filename}: {e}")
            return {'error': f'Syntax error: {e}'}
        except Exception as e:
            logger.error(f"Taint analysis failed for {filename}: {e}")
            return {'error': str(e)}

    def analyze_function(self, func) -> Dict[str, Any]:
        """
        Analyze a Python function object for taint.

        Args:
            func: Function to analyze

        Returns:
            Taint analysis results
        """
        try:
            source = inspect.getsource(func)
            filename = inspect.getfile(func)
            return self.analyze_code(source, filename)
        except Exception as e:
            logger.error(f"Function analysis failed: {e}")
            return {'error': str(e)}

    def _load_default_sources(self) -> List[TaintSource]:
        """Load default taint sources."""
        return [
            TaintSource("input", "builtin.input"),
            TaintSource("argv", "sys.argv"),
            TaintSource("environ", "os.environ"),
            TaintSource("request_data", "flask.request.data"),
            TaintSource("request_args", "flask.request.args"),
        ]

    def _load_default_sinks(self) -> List[TaintSink]:
        """Load default taint sinks."""
        return [
            TaintSink("execute", "builtin.exec", "code_injection"),
            TaintSink("eval", "builtin.eval", "code_injection"),
            TaintSink("subprocess_call", "subprocess.call", "command_injection"),
            TaintSink("sql_execute", "sqlite3.execute", "sql_injection"),
            TaintSink("file_write", "open", "file_inclusion"),
        ]

    def _classify_vulnerabilities(self, flows: List[TaintFlow]) -> List[Dict[str, Any]]:
        """Classify taint flows as vulnerabilities."""
        vulnerabilities = []
        for flow in flows:
            if flow.confidence > 0.7:  # High confidence threshold
                vulnerabilities.append({
                    'type': flow.sink.vulnerability_type,
                    'severity': 'high' if flow.confidence > 0.9 else 'medium',
                    'source': flow.source.name,
                    'sink': flow.sink.name,
                    'path': flow.path,
                    'description': f"Tainted data from {flow.source.name} reaches {flow.sink.name}"
                })
        return vulnerabilities

class TaintAnalyzer(ast.NodeVisitor):
    """
    AST visitor for taint analysis.
    """

    def __init__(self, sources: List[TaintSource], sinks: List[TaintSink]):
        self.sources = sources
        self.sinks = sinks
        self.sources_found = []
        self.sinks_found = []
        self.flows = []
        self.taint_vars = set()
        self.var_taint_map = {}

    def visit_Call(self, node):
        """Visit function calls to check for sources and sinks."""
        # Check if this is a source
        func_name = self._get_func_name(node.func)
        for source in self.sources:
            if source.name in func_name or source.location in func_name:
                self.sources_found.append(source)
                # Mark return value as tainted if assigned
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.taint_vars.add(target.id)
                            self.var_taint_map[target.id] = source

        # Check if this is a sink
        for sink in self.sinks:
            if sink.name in func_name or sink.location in func_name:
                self.sinks_found.append(sink)
                # Check if arguments are tainted
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id in self.taint_vars:
                        source = self.var_taint_map.get(arg.id)
                        if source:
                            flow = TaintFlow(
                                source=source,
                                sink=sink,
                                path=[arg.id],  # Simplified path
                                confidence=0.8
                            )
                            self.flows.append(flow)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Track taint propagation through assignments."""
        self.generic_visit(node)

        # If RHS is tainted, mark LHS as tainted
        for target in node.targets:
            if isinstance(target, ast.Name):
                if self._is_expr_tainted(node.value):
                    self.taint_vars.add(target.id)
                    # Propagate taint source
                    taint_source = self._get_expr_taint(node.value)
                    if taint_source:
                        self.var_taint_map[target.id] = taint_source

    def _get_func_name(self, node) -> str:
        """Get function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""

    def _is_expr_tainted(self, expr) -> bool:
        """Check if an expression is tainted."""
        if isinstance(expr, ast.Name):
            return expr.id in self.taint_vars
        elif isinstance(expr, ast.Call):
            # Check if call returns tainted data
            func_name = self._get_func_name(expr.func)
            for source in self.sources:
                if source.name in func_name:
                    return True
        return False

    def _get_expr_taint(self, expr) -> Optional[TaintSource]:
        """Get taint source for an expression."""
        if isinstance(expr, ast.Name):
            return self.var_taint_map.get(expr.id)
        return None