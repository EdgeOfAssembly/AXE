"""
Plane - Source/Sink Enumeration Tool
Catalogs and enumerates data sources and sinks in codebases for comprehensive analysis.
Works with static analysis to identify entry and exit points.
"""
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
logger = logging.getLogger(__name__)
@dataclass
class EnumeratedSource:
    """An enumerated data source."""
    name: str
    type: str  # 'function_call', 'variable', 'parameter', etc.
    location: str  # file:line
    context: str  # surrounding code context
    confidence: float
@dataclass
class EnumeratedSink:
    """An enumerated data sink."""
    name: str
    type: str
    location: str
    context: str
    vulnerability_potential: str  # 'high', 'medium', 'low'
    confidence: float
class PlaneEnumerator:
    """
    Source/sink enumerator for smoothing out entry and exit points in code.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.source_patterns = self._load_source_patterns()
        self.sink_patterns = self._load_sink_patterns()
    def enumerate_project(self, project_path: str) -> Dict[str, Any]:
        """
        Enumerate sources and sinks across an entire project.
        Args:
            project_path: Root path of the project to analyze
        Returns:
            Dict containing enumerated sources and sinks
        """
        project_path = Path(project_path)
        if not project_path.exists():
            return {'error': f'Project path {project_path} does not exist'}
        sources = []
        sinks = []
        # Walk through Python files
        for py_file in project_path.rglob('*.py'):
            if self._should_analyze_file(py_file):
                file_sources, file_sinks = self.enumerate_file(str(py_file))
                sources.extend(file_sources)
                sinks.extend(file_sinks)
        # Deduplicate and rank
        sources = self._deduplicate_sources(sources)
        sinks = self._deduplicate_sinks(sinks)
        return {
            'sources': [s.__dict__ for s in sources],
            'sinks': [s.__dict__ for s in sinks],
            'summary': {
                'total_sources': len(sources),
                'total_sinks': len(sinks),
                'high_risk_sinks': len([s for s in sinks if s.vulnerability_potential == 'high'])
            }
        }
    def enumerate_file(self, file_path: str) -> Tuple[List[EnumeratedSource], List[EnumeratedSink]]:
        """
        Enumerate sources and sinks in a single file.
        Args:
            file_path: Path to the file to analyze
        Returns:
            Tuple of (sources, sinks) lists
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
            enumerator = SourceSinkVisitor(file_path, self.source_patterns, self.sink_patterns)
            enumerator.visit(tree)
            return enumerator.sources, enumerator.sinks
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Enumeration failed for {file_path}: {e}")
            return [], []
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if a file should be analyzed."""
        # Skip common exclude patterns
        exclude_patterns = self.config.get('exclude_patterns', ['__pycache__', '.git', 'venv', 'node_modules'])
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                return False
        return True
    def _load_source_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for identifying sources."""
        return {
            'input': {
                'functions': ['input', 'raw_input'],
                'type': 'user_input',
                'confidence': 0.9
            },
            'argv': {
                'attributes': ['sys.argv'],
                'type': 'command_line',
                'confidence': 0.95
            },
            'environ': {
                'attributes': ['os.environ'],
                'type': 'environment',
                'confidence': 0.9
            },
            'network': {
                'functions': ['socket.recv', 'requests.get', 'urllib.request.urlopen'],
                'type': 'network_input',
                'confidence': 0.8
            },
            'file_read': {
                'functions': ['open', 'file.read', 'io.open'],
                'type': 'file_input',
                'confidence': 0.7
            }
        }
    def _load_sink_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for identifying sinks."""
        return {
            'code_execution': {
                'functions': ['exec', 'eval', 'compile'],
                'vulnerability': 'code_injection',
                'potential': 'high',
                'confidence': 0.95
            },
            'command_execution': {
                'functions': ['subprocess.call', 'subprocess.run', 'os.system', 'os.popen'],
                'vulnerability': 'command_injection',
                'potential': 'high',
                'confidence': 0.9
            },
            'sql_execution': {
                'functions': ['sqlite3.execute', 'psycopg2.execute', 'mysql.execute'],
                'vulnerability': 'sql_injection',
                'potential': 'high',
                'confidence': 0.85
            },
            'file_write': {
                'functions': ['open', 'file.write'],
                'vulnerability': 'file_inclusion',
                'potential': 'medium',
                'confidence': 0.7
            },
            'html_output': {
                'functions': ['print', 'flask.render_template'],
                'vulnerability': 'xss',
                'potential': 'medium',
                'confidence': 0.6
            }
        }
    def _deduplicate_sources(self, sources: List[EnumeratedSource]) -> List[EnumeratedSource]:
        """Remove duplicate sources."""
        seen = set()
        unique = []
        for source in sources:
            key = (source.name, source.location)
            if key not in seen:
                seen.add(key)
                unique.append(source)
        return unique
    def _deduplicate_sinks(self, sinks: List[EnumeratedSink]) -> List[EnumeratedSink]:
        """Remove duplicate sinks."""
        seen = set()
        unique = []
        for sink in sinks:
            key = (sink.name, sink.location)
            if key not in seen:
                seen.add(key)
                unique.append(sink)
        return unique
class SourceSinkVisitor(ast.NodeVisitor):
    """
    AST visitor for enumerating sources and sinks.
    """
    def __init__(self, file_path: str, source_patterns: Dict, sink_patterns: Dict):
        self.file_path = file_path
        self.source_patterns = source_patterns
        self.sink_patterns = sink_patterns
        self.sources = []
        self.sinks = []
    def visit_Call(self, node):
        """Visit function calls."""
        func_name = self._get_full_func_name(node.func)
        # Check for sources
        for pattern_name, pattern in self.source_patterns.items():
            if any(func in func_name for func in pattern.get('functions', [])):
                source = EnumeratedSource(
                    name=func_name,
                    type=pattern['type'],
                    location=f"{self.file_path}:{node.lineno}",
                    context=self._get_context(node),
                    confidence=pattern['confidence']
                )
                self.sources.append(source)
        # Check for sinks
        for pattern_name, pattern in self.sink_patterns.items():
            if any(func in func_name for func in pattern.get('functions', [])):
                sink = EnumeratedSink(
                    name=func_name,
                    type=pattern['vulnerability'],
                    location=f"{self.file_path}:{node.lineno}",
                    context=self._get_context(node),
                    vulnerability_potential=pattern['potential'],
                    confidence=pattern['confidence']
                )
                self.sinks.append(sink)
        self.generic_visit(node)
    def visit_Attribute(self, node):
        """Visit attribute access."""
        attr_name = self._get_full_attr_name(node)
        # Check for sources
        for pattern_name, pattern in self.source_patterns.items():
            if any(attr in attr_name for attr in pattern.get('attributes', [])):
                source = EnumeratedSource(
                    name=attr_name,
                    type=pattern['type'],
                    location=f"{self.file_path}:{node.lineno}",
                    context=self._get_context(node),
                    confidence=pattern['confidence']
                )
                self.sources.append(source)
        self.generic_visit(node)
    def _get_full_func_name(self, node) -> str:
        """Get full function name from call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_full_func_name(node.value)}.{node.attr}"
        return ""
    def _get_full_attr_name(self, node) -> str:
        """Get full attribute name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_full_attr_name(node.value)}.{node.attr}"
        return ""
    def _get_context(self, node) -> str:
        """Get code context around the node."""
        # Simplified context extraction
        return f"Line {node.lineno}: {ast.unparse(node)[:100]}..."