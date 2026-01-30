"""
Prompt compression utilities for AXE.
Reduces system prompt overhead while preserving essential instructions.
"""
import re
from typing import Dict, List, Any
class PromptCompressor:
    """
    Compresses system prompts to reduce token usage.
    Features:
    - Remove verbose explanations
    - Condense examples
    - Abbreviate common instructions
    - Preserve critical directives
    """
    # Common regex pattern for matching until section breaks
    # Matches content until: double newline, newline + capital letter, or end of string
    SECTION_END_PATTERN = r'(?=\n\n|\n[A-Z]|\Z)'
    def __init__(self):
        """Initialize the prompt compressor."""
        # Common abbreviations for instructions
        self.abbreviations = {
            'You are an expert': 'Expert',
            'You are a': '',
            'Please provide': 'Provide',
            'Make sure to': 'Ensure',
            'You should': '',
            'It is important to': 'Must',
            'Always remember to': 'Always',
        }
        # Patterns for removable content (using shared pattern)
        self.removable_patterns = [
            rf'(?:For example|Example):.*?{self.SECTION_END_PATTERN}',  # Remove examples
            rf'(?:Note|Important):.*?{self.SECTION_END_PATTERN}',  # Remove notes
            r'\(.*?\)',  # Remove parenthetical remarks
        ]
    def compress(self, prompt: str, level: str = 'balanced') -> str:
        """
        Compress a system prompt.
        Args:
            prompt: Original system prompt
            level: Compression level ('minimal', 'balanced', 'aggressive')
        Returns:
            Compressed prompt
        """
        if level == 'minimal':
            return self._minimal_compression(prompt)
        elif level == 'aggressive':
            return self._aggressive_compression(prompt)
        else:
            return self._balanced_compression(prompt)
    def _minimal_compression(self, prompt: str) -> str:
        """
        Minimal compression - only remove obvious redundancy.
        Args:
            prompt: Original prompt
        Returns:
            Minimally compressed prompt
        """
        # Remove excessive whitespace
        compressed = re.sub(r'\n{3,}', '\n\n', prompt)
        compressed = re.sub(r' {2,}', ' ', compressed)
        # Remove trailing whitespace
        compressed = '\n'.join(line.rstrip() for line in compressed.split('\n'))
        return compressed.strip()
    def _balanced_compression(self, prompt: str) -> str:
        """
        Balanced compression - remove redundancy and some examples.
        Args:
            prompt: Original prompt
        Returns:
            Balanced compressed prompt
        """
        compressed = prompt
        # Apply abbreviations
        for long_form, short_form in self.abbreviations.items():
            if short_form:
                compressed = compressed.replace(long_form, short_form)
            else:
                # Remove entirely
                compressed = re.sub(rf'{re.escape(long_form)}\s+', '', compressed)
        # Remove parenthetical remarks
        compressed = re.sub(r'\s*\([^)]{20,}\)', '', compressed)
        # Condense examples (keep first 2)
        compressed = self._condense_examples(compressed, keep=2)
        # Clean whitespace
        compressed = re.sub(r'\n{3,}', '\n\n', compressed)
        compressed = re.sub(r' {2,}', ' ', compressed)
        return compressed.strip()
    def _aggressive_compression(self, prompt: str) -> str:
        """
        Aggressive compression - maximum reduction while preserving meaning.
        Args:
            prompt: Original prompt
        Returns:
            Aggressively compressed prompt
        """
        compressed = prompt
        # Apply all abbreviations
        for long_form, short_form in self.abbreviations.items():
            if short_form:
                compressed = compressed.replace(long_form, short_form)
            else:
                compressed = re.sub(rf'{re.escape(long_form)}\s+', '', compressed)
        # Remove all parenthetical remarks
        compressed = re.sub(r'\s*\([^)]*\)', '', compressed)
        # Remove examples entirely (using shared pattern)
        compressed = re.sub(rf'(?:For example|Example):.*?{self.SECTION_END_PATTERN}', '', compressed, flags=re.DOTALL | re.IGNORECASE)
        # Remove notes (using shared pattern)
        compressed = re.sub(rf'(?:Note|Important):.*?{self.SECTION_END_PATTERN}', '', compressed, flags=re.DOTALL | re.IGNORECASE)
        # Convert bullet lists to comma-separated
        compressed = self._condense_lists(compressed)
        # Remove verbose phrases
        verbose_phrases = [
            'in order to', 'for the purpose of', 'with the goal of',
            'it should be noted that', 'please be aware that',
            'as mentioned previously', 'as stated above'
        ]
        for phrase in verbose_phrases:
            compressed = re.sub(rf'\s*{re.escape(phrase)}\s*', ' ', compressed, flags=re.IGNORECASE)
        # Clean whitespace
        compressed = re.sub(r'\n{3,}', '\n\n', compressed)
        compressed = re.sub(r' {2,}', ' ', compressed)
        compressed = re.sub(r'\n ', '\n', compressed)
        return compressed.strip()
    def _condense_examples(self, text: str, keep: int = 2) -> str:
        """
        Reduce number of examples in text.
        Args:
            text: Text with examples
            keep: Number of examples to keep
        Returns:
            Text with condensed examples
        """
        def shorten_section(match):
            header = match.group(1)
            content = match.group(2)
            # Split into individual examples
            examples = re.split(r'\n\s*[-*•]\s+', content)
            examples = [e.strip() for e in examples if e.strip()]
            if len(examples) <= keep:
                return match.group(0)
            # Keep first N examples
            kept_examples = examples[:keep]
            omitted = len(examples) - keep
            result = f"{header}\n"
            for ex in kept_examples:
                result += f"- {ex}\n"
            result += f"[{omitted} more examples omitted]\n"
            return result
        # Use shared pattern for consistency
        pattern = rf'((?:Examples?|For example):)\s*(.*?){self.SECTION_END_PATTERN}'
        return re.sub(pattern, shorten_section, text, flags=re.DOTALL | re.IGNORECASE)
    def _condense_lists(self, text: str) -> str:
        """
        Convert bullet lists to comma-separated format where appropriate.
        Args:
            text: Text with bullet lists
        Returns:
            Text with condensed lists
        """
        def condense_list(match):
            items = re.findall(r'[-*•]\s+([^\n]+)', match.group(0))
            # Only condense short lists
            if len(items) <= 1 or any(len(item) > 50 for item in items):
                return match.group(0)
            # Convert to comma-separated
            return ', '.join(items) + '.\n'
        # Match bullet lists
        pattern = r'(?:^|\n)((?:\s*[-*•]\s+[^\n]+\n)+)'
        return re.sub(pattern, condense_list, text, flags=re.MULTILINE)
    def extract_critical_directives(self, prompt: str) -> List[str]:
        """
        Extract critical directives from a prompt.
        Args:
            prompt: System prompt
        Returns:
            List of critical directives
        """
        directives = []
        # Patterns for critical instructions
        critical_patterns = [
            r'(?:Must|Always|Never|Do not)\s+[^.!?\n]+[.!?]',
            r'(?:Required|Essential|Critical):\s*[^.\n]+',
            r'IMPORTANT:\s*[^.\n]+',
        ]
        for pattern in critical_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            directives.extend(matches)
        return directives
    def create_minimal_prompt(self, role: str, critical_only: bool = False) -> str:
        """
        Create a minimal prompt for an agent role.
        Args:
            role: Agent role description
            critical_only: If True, only include critical directives
        Returns:
            Minimal prompt
        """
        base_prompts = {
            'coder': 'Expert coder. Provide working code. Follow best practices.',
            'reviewer': 'Code reviewer. Find bugs, security issues, improvements.',
            'analyzer': 'Code analyzer. Analyze structure, patterns, dependencies.',
            'security': 'Security auditor. Find vulnerabilities, suggest fixes.',
            'optimizer': 'Performance optimizer. Improve speed, memory, efficiency.',
        }
        # Try to match role to base prompt
        role_lower = role.lower()
        for key, prompt in base_prompts.items():
            if key in role_lower:
                return prompt
        # Generic minimal prompt
        return f'{role}. Provide clear, concise responses.'
    def compress_workshop_instructions(self, prompt: str) -> str:
        """
        Compress workshop tool instructions in prompts.
        Args:
            prompt: Prompt with workshop instructions
        Returns:
            Compressed prompt
        """
        # Condense workshop tool descriptions
        # Pattern matches "Workshop tools available:" followed by tool descriptions until double newline or end
        workshop_pattern = r'(Workshop tools available:)(.*?)(?=\n\n|\Z)'
        def condense_workshop(match):
            intro = match.group(1)
            tools = match.group(2)
            # Extract tool names and purposes from patterns like "/workshop chisel for symbolic execution"
            # Captures: tool name (word) and purpose (text after "for" or "to")
            tool_info = re.findall(r'/workshop\s+(\w+)[^,;.]*?(?:for|to)\s+([^,;.\n]+)', tools)
            if not tool_info:
                return match.group(0)
            # Create condensed list in format: name(purpose), name(purpose), ...
            condensed = intro + ' ' + ', '.join(f'{name}({purpose.strip()})' for name, purpose in tool_info[:4])
            if len(tool_info) > 4:
                condensed += f' +{len(tool_info)-4} more'
            return condensed
        return re.sub(workshop_pattern, condense_workshop, prompt, flags=re.DOTALL | re.IGNORECASE)
def calculate_compression_ratio(original: str, compressed: str) -> Dict[str, Any]:
    """
    Calculate compression statistics.
    Args:
        original: Original prompt
        compressed: Compressed prompt
    Returns:
        Dictionary with compression statistics
    """
    original_len = len(original)
    compressed_len = len(compressed)
    if original_len == 0:
        return {
            'original_length': 0,
            'compressed_length': 0,
            'saved_chars': 0,
            'compression_ratio': 0.0,
            'percent_saved': 0.0
        }
    saved = original_len - compressed_len
    ratio = compressed_len / original_len
    percent = (saved / original_len) * 100
    return {
        'original_length': original_len,
        'compressed_length': compressed_len,
        'saved_chars': saved,
        'compression_ratio': ratio,
        'percent_saved': percent
    }
def compress_system_prompts(config: Dict) -> Dict:
    """
    Compress all system prompts in a configuration.
    Args:
        config: AXE configuration dictionary
    Returns:
        Configuration with compressed prompts
    """
    compressor = PromptCompressor()
    compressed_config = config.copy()
    if 'agents' not in compressed_config:
        return compressed_config
    for agent_name, agent_config in compressed_config['agents'].items():
        if 'system_prompt' in agent_config:
            original = agent_config['system_prompt']
            compressed = compressor.compress(original, level='balanced')
            agent_config['system_prompt'] = compressed
    return compressed_config