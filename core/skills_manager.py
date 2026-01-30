"""
Skills Manager for AXE.
Manages agent skills - loading, discovery, and injection into prompts.
Supports keyword-based activation and provider-specific filtering.
"""
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
@dataclass
class Skill:
    """Represents a single agent skill."""
    name: str
    filename: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=lambda: ["all"])
    def matches_keyword(self, text: str) -> bool:
        """Check if any keyword matches the given text (case-insensitive)."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
    def supports_provider(self, provider: str) -> bool:
        """Check if skill supports the given provider."""
        return "all" in self.providers or provider in self.providers
class SkillsManager:
    """Manager for Agent Skills system."""
    def __init__(self, skills_dir: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the Skills Manager.
        Args:
            skills_dir: Path to skills directory (relative or absolute).
                       Defaults to "skills" in current directory if None or empty.
            config: Optional configuration dictionary for skills
        """
        # Handle None or empty skills_dir with proper default
        if skills_dir is None or skills_dir == '':
            skills_dir = "skills"
        self.skills_dir = skills_dir
        self.config = config or {}
        self.skills_cache: Dict[str, Skill] = {}
        self.manifest: Dict[str, Any] = {}
        # Make skills_dir absolute if relative
        if not os.path.isabs(self.skills_dir):
            # Assume relative to current working directory
            self.skills_dir = os.path.join(os.getcwd(), self.skills_dir)
        # Load manifest and discover skills
        self._load_manifest()
        self._discover_skills()
    def _load_manifest(self) -> None:
        """Load skills/manifest.json if it exists."""
        manifest_path = os.path.join(self.skills_dir, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    self.manifest = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load manifest.json: {e}")
                self.manifest = {}
        else:
            self.manifest = {}
    def _discover_skills(self) -> None:
        """Auto-discover .md skill files in skills directory."""
        if not os.path.exists(self.skills_dir):
            print(f"Warning: Skills directory '{self.skills_dir}' not found")
            return
        # Find all .md files
        skills_path = Path(self.skills_dir)
        for md_file in skills_path.glob("*.md"):
            skill_name = md_file.stem  # filename without .md extension
            try:
                # Load skill content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Get metadata from manifest if available
                manifest_skills = self.manifest.get('skills', {})
                skill_metadata = manifest_skills.get(skill_name, {})
                # Extract keywords and providers from metadata
                keywords = skill_metadata.get('keywords', [skill_name])
                providers = skill_metadata.get('providers', ['all'])
                # Create Skill object
                skill = Skill(
                    name=skill_name,
                    filename=str(md_file),
                    content=content,
                    metadata=skill_metadata,
                    keywords=keywords,
                    providers=providers
                )
                self.skills_cache[skill_name] = skill
            except Exception as e:
                print(f"Warning: Failed to load skill '{skill_name}': {e}")
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get skill by name.
        Args:
            name: Skill name (without .md extension)
        Returns:
            Skill object or None if not found
        """
        return self.skills_cache.get(name)
    def get_all_skills(self) -> List[Skill]:
        """Get all loaded skills."""
        return list(self.skills_cache.values())
    def get_skills_for_task(self, task_description: str, provider: Optional[str] = None) -> List[Skill]:
        """
        Get relevant skills based on task keywords and provider.
        Args:
            task_description: Description of the task (e.g., user prompt)
            provider: Optional provider name to filter by (e.g., 'anthropic', 'openai')
        Returns:
            List of matching Skill objects
        """
        matching_skills = []
        for skill in self.skills_cache.values():
            # Check provider compatibility
            if provider and not skill.supports_provider(provider):
                continue
            # Check keyword match
            if skill.matches_keyword(task_description):
                matching_skills.append(skill)
        return matching_skills
    def get_skills_by_names(self, names: List[str], provider: Optional[str] = None) -> List[Skill]:
        """
        Get skills by explicit names.
        Args:
            names: List of skill names to retrieve
            provider: Optional provider name to filter by
        Returns:
            List of Skill objects (skips non-existent skills)
        """
        skills = []
        for name in names:
            skill = self.get_skill(name)
            if skill:
                # Check provider compatibility if specified
                if provider and not skill.supports_provider(provider):
                    continue
                skills.append(skill)
        return skills
    def inject_skills_to_prompt(self, system_prompt: str, skills: List[Skill]) -> str:
        """
        Inject skill content into system prompt efficiently.
        Args:
            system_prompt: Original system prompt
            skills: List of skills to inject
        Returns:
            Enhanced system prompt with skills injected
        """
        if not skills:
            return system_prompt
        # Build skills section
        skills_section = "\n\n# AGENT SKILLS\n\n"
        skills_section += "You have been enhanced with the following specialized skills:\n\n"
        for skill in skills:
            skills_section += f"## {skill.metadata.get('name', skill.name)}\n\n"
            skills_section += skill.content
            skills_section += "\n\n---\n\n"
        # Append to system prompt
        return system_prompt + skills_section
    def get_skill_metadata_only(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get skill metadata without full content (for token efficiency).
        Args:
            name: Skill name
        Returns:
            Dictionary with metadata or None if not found
        """
        skill = self.get_skill(name)
        if skill:
            return {
                'name': skill.name,
                'description': skill.metadata.get('description', ''),
                'keywords': skill.keywords,
                'providers': skill.providers,
                'filename': skill.filename
            }
        return None
    def get_activation_keywords(self) -> Dict[str, List[str]]:
        """
        Get all activation keywords mapped to skill names.
        Returns:
            Dictionary mapping skill names to their keywords
        """
        return {
            skill.name: skill.keywords
            for skill in self.skills_cache.values()
        }
def create_skills_manager(skills_dir: Optional[str] = None, config: Optional[Dict] = None) -> SkillsManager:
    """
    Factory function to create a SkillsManager instance.
    Args:
        skills_dir: Path to skills directory. Defaults to "skills" if None or empty.
        config: Optional configuration dictionary
    Returns:
        Initialized SkillsManager instance
    """
    return SkillsManager(skills_dir=skills_dir, config=config)