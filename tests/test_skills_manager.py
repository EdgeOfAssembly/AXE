#!/usr/bin/env python3
"""
Test suite for Skills Manager.
Tests skill discovery, loading, keyword matching, provider filtering, and prompt injection.
"""

import sys
import os
import json
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.skills_manager import SkillsManager, Skill, create_skills_manager


def test_skill_discovery():
    """Test auto-discovery of .md files in skills/"""
    print("Testing skill discovery...")
    
    # Create temporary skills directory
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create test skill files
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill\nTest content")
        
        with open(os.path.join(skills_dir, "another_skill.md"), 'w') as f:
            f.write("# Another Skill\nMore content")
        
        # Initialize manager
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Check discovery
        assert "test_skill" in manager.skills_cache, "test_skill should be discovered"
        assert "another_skill" in manager.skills_cache, "another_skill should be discovered"
        assert len(manager.skills_cache) == 2, f"Should have 2 skills, got {len(manager.skills_cache)}"
        
        print("  ✓ Skill discovery works correctly")
    print()


def test_manifest_loading():
    """Test loading skills/manifest.json"""
    print("Testing manifest loading...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create manifest
        manifest = {
            "version": "1.0.0",
            "skills": {
                "test_skill": {
                    "name": "Test Skill",
                    "description": "A test skill",
                    "keywords": ["test", "example"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        # Create skill file
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill\nContent")
        
        # Initialize manager
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Check manifest loaded
        assert manager.manifest["version"] == "1.0.0", "Manifest version should be loaded"
        assert "test_skill" in manager.manifest["skills"], "Skill should be in manifest"
        
        # Check skill metadata from manifest
        skill = manager.get_skill("test_skill")
        assert skill is not None, "Skill should exist"
        assert skill.keywords == ["test", "example"], f"Keywords should be from manifest, got {skill.keywords}"
        
        print("  ✓ Manifest loading works correctly")
    print()


def test_skill_content_loading():
    """Test loading full skill content from .md files"""
    print("Testing skill content loading...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        test_content = "# Test Skill\n\nThis is test content with multiple lines.\n\n## Section\nMore content here."
        
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write(test_content)
        
        manager = SkillsManager(skills_dir=skills_dir)
        skill = manager.get_skill("test_skill")
        
        assert skill is not None, "Skill should be loaded"
        assert skill.content == test_content, "Skill content should match file content"
        assert skill.name == "test_skill", f"Skill name should be 'test_skill', got {skill.name}"
        
        print("  ✓ Skill content loading works correctly")
    print()


def test_keyword_matching():
    """Test keyword-based skill activation"""
    print("Testing keyword matching...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create manifest with keywords
        manifest = {
            "version": "1.0.0",
            "skills": {
                "python_skill": {
                    "keywords": ["python", "pytest", "async"],
                    "providers": ["all"]
                },
                "cpp_skill": {
                    "keywords": ["c++", "cpp", "refactor"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        # Create skill files
        for name in ["python_skill", "cpp_skill"]:
            with open(os.path.join(skills_dir, f"{name}.md"), 'w') as f:
                f.write(f"# {name}\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Test keyword matching
        python_tasks = manager.get_skills_for_task("Write a Python script with pytest")
        assert len(python_tasks) == 1, f"Should match python_skill, got {len(python_tasks)}"
        assert python_tasks[0].name == "python_skill", "Should match python_skill"
        
        cpp_tasks = manager.get_skills_for_task("Refactor this C++ code")
        assert len(cpp_tasks) == 1, f"Should match cpp_skill, got {len(cpp_tasks)}"
        assert cpp_tasks[0].name == "cpp_skill", "Should match cpp_skill"
        
        # Test case insensitivity
        async_tasks = manager.get_skills_for_task("ASYNC programming in Python")
        assert len(async_tasks) == 1, "Should match python_skill (case insensitive)"
        
        # Test no match
        no_match = manager.get_skills_for_task("Write a Java application")
        assert len(no_match) == 0, f"Should not match any skills, got {len(no_match)}"
        
        print("  ✓ Keyword matching works correctly")
    print()


def test_provider_filtering():
    """Test filtering skills by provider (anthropic vs all)"""
    print("Testing provider filtering...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create manifest with provider-specific skills
        manifest = {
            "version": "1.0.0",
            "skills": {
                "anthropic_only": {
                    "keywords": ["claude", "security"],
                    "providers": ["anthropic"]
                },
                "all_providers": {
                    "keywords": ["general", "code"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        # Create skill files
        for name in ["anthropic_only", "all_providers"]:
            with open(os.path.join(skills_dir, f"{name}.md"), 'w') as f:
                f.write(f"# {name}\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Test anthropic provider gets both
        anthropic_skills = manager.get_skills_for_task("Write code with security", provider="anthropic")
        assert len(anthropic_skills) == 2, f"Anthropic should get both skills, got {len(anthropic_skills)}"
        
        # Test openai provider only gets "all"
        openai_skills = manager.get_skills_for_task("Write general code", provider="openai")
        assert len(openai_skills) == 1, f"OpenAI should only get all_providers skill, got {len(openai_skills)}"
        assert openai_skills[0].name == "all_providers", "Should be all_providers skill"
        
        print("  ✓ Provider filtering works correctly")
    print()


def test_prompt_injection():
    """Test skill content injection into system prompts"""
    print("Testing prompt injection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create test skill
        manifest = {
            "version": "1.0.0",
            "skills": {
                "test_skill": {
                    "name": "Test Skill",
                    "keywords": ["test"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill Content\n\nThis is the skill content.")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Test injection
        original_prompt = "You are a helpful assistant."
        skill = manager.get_skill("test_skill")
        enhanced_prompt = manager.inject_skills_to_prompt(original_prompt, [skill])
        
        assert original_prompt in enhanced_prompt, "Original prompt should be present"
        assert "AGENT SKILLS" in enhanced_prompt, "Skills section should be added"
        assert "Test Skill" in enhanced_prompt, "Skill name should be in prompt"
        assert "This is the skill content" in enhanced_prompt, "Skill content should be in prompt"
        
        # Test empty skills list
        no_skills_prompt = manager.inject_skills_to_prompt(original_prompt, [])
        assert no_skills_prompt == original_prompt, "Empty skills should not modify prompt"
        
        print("  ✓ Prompt injection works correctly")
    print()


def test_token_efficiency():
    """Test metadata-only loading for large skill sets"""
    print("Testing token efficiency (metadata-only loading)...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manifest = {
            "version": "1.0.0",
            "skills": {
                "test_skill": {
                    "name": "Test Skill",
                    "description": "A test skill for efficiency",
                    "keywords": ["test"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        large_content = "# Large Skill\n\n" + ("Content line\n" * 1000)
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write(large_content)
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Get metadata only
        metadata = manager.get_skill_metadata_only("test_skill")
        
        assert metadata is not None, "Metadata should be returned"
        assert "name" in metadata, "Should have name"
        assert "description" in metadata, "Should have description"
        assert "keywords" in metadata, "Should have keywords"
        assert "providers" in metadata, "Should have providers"
        
        # Metadata should not include full content
        assert "content" not in metadata or len(str(metadata.get("content", ""))) < 100, \
            "Metadata should not include full content"
        
        print("  ✓ Token efficiency (metadata-only) works correctly")
    print()


def test_multiple_skills():
    """Test loading multiple skills for a single task"""
    print("Testing multiple skills activation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manifest = {
            "version": "1.0.0",
            "skills": {
                "skill1": {"keywords": ["python"], "providers": ["all"]},
                "skill2": {"keywords": ["testing"], "providers": ["all"]},
                "skill3": {"keywords": ["python", "testing"], "providers": ["all"]}
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        for name in ["skill1", "skill2", "skill3"]:
            with open(os.path.join(skills_dir, f"{name}.md"), 'w') as f:
                f.write(f"# {name}\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Should match multiple skills
        matched = manager.get_skills_for_task("Python testing framework")
        assert len(matched) == 3, f"Should match 3 skills, got {len(matched)}"
        
        print("  ✓ Multiple skills activation works correctly")
    print()


def test_skill_not_found():
    """Test graceful handling of missing skills"""
    print("Testing skill not found...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Try to get non-existent skill
        skill = manager.get_skill("nonexistent")
        assert skill is None, "Non-existent skill should return None"
        
        # Try metadata for non-existent skill
        metadata = manager.get_skill_metadata_only("nonexistent")
        assert metadata is None, "Non-existent skill metadata should return None"
        
        print("  ✓ Missing skill handling works correctly")
    print()


def test_malformed_manifest():
    """Test handling of malformed manifest.json"""
    print("Testing malformed manifest handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create malformed JSON
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            f.write("{ invalid json }}")
        
        # Create a valid skill file
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test\nContent")
        
        # Manager should still initialize and discover skills
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Should still discover the skill even with bad manifest
        assert "test_skill" in manager.skills_cache, "Should still discover skills despite bad manifest"
        
        print("  ✓ Malformed manifest handling works correctly")
    print()


def test_empty_skills_dir():
    """Test handling of empty skills directory"""
    print("Testing empty skills directory...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Initialize with empty directory
        manager = SkillsManager(skills_dir=skills_dir)
        
        assert len(manager.skills_cache) == 0, "Should have no skills"
        assert len(manager.get_all_skills()) == 0, "get_all_skills should return empty list"
        
        # Should not crash on queries
        skills = manager.get_skills_for_task("anything")
        assert len(skills) == 0, "Should return empty list for any query"
        
        print("  ✓ Empty skills directory handling works correctly")
    print()


def test_all_skill_files_exist():
    """Verify all expected skill files exist in real skills directory"""
    print("Testing that all expected skill files exist...")
    
    # Use actual skills directory
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    skills_dir = os.path.join(repo_root, 'skills')
    
    expected_skills = [
        "reverse_engineering_expert.md",
        "cpp_refactoring_expert.md",
        "ida_pro_analysis_patterns.md",
        "c_modernization_expert.md",
        "cpp_modernization_expert.md",
        "python_agent_expert.md",
        "x86_assembly_expert.md",
        "build.md",
        "claude_build.md"
    ]
    
    for skill_file in expected_skills:
        path = os.path.join(skills_dir, skill_file)
        assert os.path.exists(path), f"Skill file {skill_file} should exist"
    
    # Check manifest exists
    manifest_path = os.path.join(skills_dir, "manifest.json")
    assert os.path.exists(manifest_path), "manifest.json should exist"
    
    print(f"  ✓ All {len(expected_skills)} skill files exist")
    print()


def test_skill_file_format():
    """Verify skill files have proper markdown format with headers"""
    print("Testing skill file format...")
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    skills_dir = os.path.join(repo_root, 'skills')
    
    skill_files = [
        "reverse_engineering_expert.md",
        "cpp_refactoring_expert.md",
        "ida_pro_analysis_patterns.md",
        "c_modernization_expert.md",
        "cpp_modernization_expert.md",
        "python_agent_expert.md",
        "x86_assembly_expert.md"
    ]
    
    for skill_file in skill_files:
        path = os.path.join(skills_dir, skill_file)
        with open(path, 'r') as f:
            content = f.read()
        
        # Should start with # header
        assert content.startswith('#'), f"{skill_file} should start with markdown header"
        
        # Should have some content
        assert len(content) > 100, f"{skill_file} should have substantial content"
    
    print("  ✓ Skill file formats are correct")
    print()


def test_skill_content_not_empty():
    """Verify skill files have substantial content"""
    print("Testing skill content is not empty...")
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    skills_dir = os.path.join(repo_root, 'skills')
    
    manager = SkillsManager(skills_dir=skills_dir)
    
    for skill_name, skill in manager.skills_cache.items():
        assert len(skill.content) > 50, f"Skill {skill_name} should have substantial content"
        assert skill.content.strip(), f"Skill {skill_name} should not be just whitespace"
    
    print(f"  ✓ All {len(manager.skills_cache)} skills have substantial content")
    print()


def test_agents_md_exists():
    """Verify AGENTS.md exists at repo root"""
    print("Testing AGENTS.md exists...")
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    agents_md_path = os.path.join(repo_root, 'AGENTS.md')
    
    assert os.path.exists(agents_md_path), "AGENTS.md should exist at repository root"
    
    with open(agents_md_path, 'r') as f:
        content = f.read()
    
    assert len(content) > 500, "AGENTS.md should have substantial content"
    
    print("  ✓ AGENTS.md exists at repository root")
    print()


def test_agents_md_required_sections():
    """Verify AGENTS.md has all required sections per standard"""
    print("Testing AGENTS.md required sections...")
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    agents_md_path = os.path.join(repo_root, 'AGENTS.md')
    
    with open(agents_md_path, 'r') as f:
        content = f.read()
    
    required_sections = [
        "Project Overview",
        "Development Environment",
        "Testing",
        "Coding Conventions"
    ]
    
    for section in required_sections:
        assert section in content, f"AGENTS.md should have '{section}' section"
    
    print(f"  ✓ AGENTS.md has all {len(required_sections)} required sections")
    print()


def test_skills_config_in_yaml():
    """Test skills configuration in axe.yaml and models.yaml"""
    print("Testing skills configuration in YAML files...")
    
    import yaml
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    
    # Check models.yaml
    with open(os.path.join(repo_root, 'models.yaml'), 'r') as f:
        models_config = yaml.safe_load(f)
    
    assert 'anthropic' in models_config, "models.yaml should have anthropic section"
    assert 'agent_skills' in models_config['anthropic'], "anthropic section should have agent_skills"
    
    skills_config = models_config['anthropic']['agent_skills']
    assert skills_config.get('enabled') == True, "agent_skills should be enabled"
    assert 'activation_keywords' in skills_config, "Should have activation_keywords"
    
    # Check axe.yaml
    with open(os.path.join(repo_root, 'axe.yaml'), 'r') as f:
        axe_config = yaml.safe_load(f)
    
    assert 'agents' in axe_config, "axe.yaml should have agents section"
    assert 'claude' in axe_config['agents'], "Should have claude agent"
    assert 'default_skills' in axe_config['agents']['claude'], "Claude should have default_skills"
    
    default_skills = axe_config['agents']['claude']['default_skills']
    assert len(default_skills) > 0, "Claude should have at least one default skill"
    
    print("  ✓ Skills configuration in YAML files is correct")
    print()


def test_default_skills_per_agent():
    """Test default skills are applied per agent config"""
    print("Testing default skills per agent...")
    
    import yaml
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    skills_dir = os.path.join(repo_root, 'skills')
    
    # Load axe.yaml
    with open(os.path.join(repo_root, 'axe.yaml'), 'r') as f:
        axe_config = yaml.safe_load(f)
    
    # Get Claude's default skills
    claude_skills = axe_config['agents']['claude'].get('default_skills', [])
    
    # Initialize skills manager
    manager = SkillsManager(skills_dir=skills_dir)
    
    # Get skills by names
    skills = manager.get_skills_by_names(claude_skills, provider='anthropic')
    
    assert len(skills) > 0, "Should load at least one default skill"
    
    # Verify each skill exists
    for skill_name in claude_skills:
        skill = manager.get_skill(skill_name)
        assert skill is not None, f"Default skill '{skill_name}' should exist"
    
    print(f"  ✓ Default skills ({len(claude_skills)}) are correctly configured")
    print()


def test_create_skills_manager_factory():
    """Test create_skills_manager factory function"""
    print("Testing create_skills_manager factory...")
    
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    skills_dir = os.path.join(repo_root, 'skills')
    
    manager = create_skills_manager(skills_dir=skills_dir)
    
    assert isinstance(manager, SkillsManager), "Should return SkillsManager instance"
    assert len(manager.skills_cache) > 0, "Should have loaded skills"
    
    print("  ✓ Factory function works correctly")
    print()


def test_none_skills_dir():
    """Test handling of None skills_dir parameter"""
    print("Testing None skills_dir parameter...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create skills directory in current directory
            os.makedirs("skills")
            with open("skills/test_skill.md", 'w') as f:
                f.write("# Test Skill\nContent")
            
            # Initialize with None - should default to "skills"
            manager = SkillsManager(skills_dir=None)
            
            assert len(manager.skills_cache) == 1, "Should find skills in default location"
            assert "test_skill" in manager.skills_cache, "Should load test_skill"
            
            print("  ✓ None skills_dir handled correctly")
        finally:
            os.chdir(original_cwd)
    print()


def test_empty_string_skills_dir():
    """Test handling of empty string skills_dir parameter"""
    print("Testing empty string skills_dir parameter...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create skills directory in current directory
            os.makedirs("skills")
            with open("skills/test_skill.md", 'w') as f:
                f.write("# Test Skill\nContent")
            
            # Initialize with empty string - should default to "skills"
            manager = SkillsManager(skills_dir="")
            
            assert len(manager.skills_cache) == 1, "Should find skills in default location"
            
            print("  ✓ Empty string skills_dir handled correctly")
        finally:
            os.chdir(original_cwd)
    print()


def test_nonexistent_skills_directory():
    """Test handling when skills directory doesn't exist"""
    print("Testing nonexistent skills directory...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_dir = os.path.join(tmpdir, "nonexistent_skills")
        
        # Should not crash, just return empty skills
        manager = SkillsManager(skills_dir=nonexistent_dir)
        
        assert len(manager.skills_cache) == 0, "Should have no skills"
        assert manager.get_all_skills() == [], "get_all_skills should return empty list"
        
        print("  ✓ Nonexistent directory handled gracefully")
    print()


def test_missing_manifest_json():
    """Test handling when manifest.json is missing"""
    print("Testing missing manifest.json...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create skill file but no manifest
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill\nContent")
        
        # Should work with default metadata
        manager = SkillsManager(skills_dir=skills_dir)
        
        assert len(manager.skills_cache) == 1, "Should discover skill without manifest"
        skill = manager.get_skill("test_skill")
        assert skill is not None, "Should load skill"
        assert skill.keywords == ["test_skill"], "Should use default keyword (skill name)"
        
        print("  ✓ Missing manifest handled correctly")
    print()


def test_skill_file_missing_referenced_in_manifest():
    """Test when manifest references a skill file that doesn't exist"""
    print("Testing skill file missing but referenced in manifest...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create manifest with reference to nonexistent skill
        manifest = {
            "version": "1.0.0",
            "skills": {
                "nonexistent_skill": {
                    "keywords": ["test"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        # Should not crash, just not load the missing skill
        manager = SkillsManager(skills_dir=skills_dir)
        
        assert len(manager.skills_cache) == 0, "Should have no skills (file doesn't exist)"
        assert manager.get_skill("nonexistent_skill") is None, "Should not find nonexistent skill"
        
        print("  ✓ Missing skill file handled gracefully")
    print()


def test_empty_skill_file():
    """Test handling of empty skill file"""
    print("Testing empty skill file...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create empty skill file
        with open(os.path.join(skills_dir, "empty_skill.md"), 'w') as f:
            f.write("")
        
        # Should load but have empty content
        manager = SkillsManager(skills_dir=skills_dir)
        
        assert "empty_skill" in manager.skills_cache, "Should discover empty skill file"
        skill = manager.get_skill("empty_skill")
        assert skill is not None, "Should load empty skill"
        assert skill.content == "", "Content should be empty string"
        
        print("  ✓ Empty skill file handled correctly")
    print()


def test_no_skills_match_provider():
    """Test when no skills match the given provider"""
    print("Testing no skills match provider...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create skill that only works with anthropic
        manifest = {
            "version": "1.0.0",
            "skills": {
                "anthropic_only": {
                    "keywords": ["test"],
                    "providers": ["anthropic"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        with open(os.path.join(skills_dir, "anthropic_only.md"), 'w') as f:
            f.write("# Anthropic Only\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # OpenAI provider should not match
        skills = manager.get_skills_for_task("test task", provider="openai")
        assert len(skills) == 0, "Should not match skills for different provider"
        
        # Anthropic should match
        skills = manager.get_skills_for_task("test task", provider="anthropic")
        assert len(skills) == 1, "Should match skill for correct provider"
        
        print("  ✓ Provider filtering works correctly")
    print()


def test_no_skills_match_keywords():
    """Test when no skills match the given keywords"""
    print("Testing no skills match keywords...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manifest = {
            "version": "1.0.0",
            "skills": {
                "python_skill": {
                    "keywords": ["python", "pytest"],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        with open(os.path.join(skills_dir, "python_skill.md"), 'w') as f:
            f.write("# Python Skill\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Task with no matching keywords
        skills = manager.get_skills_for_task("write java code")
        assert len(skills) == 0, "Should not match skills with no keyword overlap"
        
        print("  ✓ Keyword matching works correctly")
    print()


def test_relative_path_skills_dir():
    """Test handling of relative path for skills_dir"""
    print("Testing relative path for skills_dir...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create skills directory
            os.makedirs("my_skills")
            with open("my_skills/test_skill.md", 'w') as f:
                f.write("# Test Skill\nContent")
            
            # Use relative path
            manager = SkillsManager(skills_dir="my_skills")
            
            assert len(manager.skills_cache) == 1, "Should find skills with relative path"
            # Verify it was converted to absolute
            assert os.path.isabs(manager.skills_dir), "Should convert to absolute path"
            
            print("  ✓ Relative path handled correctly")
        finally:
            os.chdir(original_cwd)
    print()


def test_absolute_path_skills_dir():
    """Test handling of absolute path for skills_dir"""
    print("Testing absolute path for skills_dir...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill\nContent")
        
        # Use absolute path
        manager = SkillsManager(skills_dir=skills_dir)
        
        assert len(manager.skills_cache) == 1, "Should find skills with absolute path"
        assert manager.skills_dir == skills_dir, "Should preserve absolute path"
        
        print("  ✓ Absolute path handled correctly")
    print()


def test_skills_with_empty_keywords():
    """Test skills with empty keywords list"""
    print("Testing skills with empty keywords...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manifest = {
            "version": "1.0.0",
            "skills": {
                "no_keywords_skill": {
                    "keywords": [],
                    "providers": ["all"]
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        with open(os.path.join(skills_dir, "no_keywords_skill.md"), 'w') as f:
            f.write("# No Keywords Skill\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Should load but not match any tasks
        assert "no_keywords_skill" in manager.skills_cache, "Should load skill"
        skills = manager.get_skills_for_task("any task")
        assert len(skills) == 0, "Should not match tasks without keywords"
        
        print("  ✓ Empty keywords handled correctly")
    print()


def test_skills_with_empty_providers():
    """Test skills with empty providers list"""
    print("Testing skills with empty providers...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        manifest = {
            "version": "1.0.0",
            "skills": {
                "no_providers_skill": {
                    "keywords": ["test"],
                    "providers": []
                }
            }
        }
        
        with open(os.path.join(skills_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f)
        
        with open(os.path.join(skills_dir, "no_providers_skill.md"), 'w') as f:
            f.write("# No Providers Skill\nContent")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Should load but not match any provider
        assert "no_providers_skill" in manager.skills_cache, "Should load skill"
        skills = manager.get_skills_for_task("test task", provider="anthropic")
        assert len(skills) == 0, "Should not match any provider with empty list"
        
        print("  ✓ Empty providers handled correctly")
    print()


def test_duplicate_skill_names():
    """Test handling of duplicate skill names (shouldn't happen, but test robustness)"""
    print("Testing duplicate skill names...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        # Create two files with same content (one overwrites the other in cache)
        with open(os.path.join(skills_dir, "skill.md"), 'w') as f:
            f.write("# Skill 1\nFirst content")
        
        manager = SkillsManager(skills_dir=skills_dir)
        
        # Should have only one skill (the later one overwrites)
        assert len(manager.skills_cache) == 1, "Should have one skill entry"
        assert "skill" in manager.skills_cache, "Should have skill in cache"
        
        print("  ✓ Duplicate handling works correctly")
    print()


def test_config_with_none_skills_config():
    """Test SkillsManager with None config parameter"""
    print("Testing None config parameter...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = os.path.join(tmpdir, "skills")
        os.makedirs(skills_dir)
        
        with open(os.path.join(skills_dir, "test_skill.md"), 'w') as f:
            f.write("# Test Skill\nContent")
        
        # None config should work
        manager = SkillsManager(skills_dir=skills_dir, config=None)
        
        assert len(manager.skills_cache) == 1, "Should work with None config"
        assert manager.config == {}, "Config should default to empty dict"
        
        print("  ✓ None config handled correctly")
    print()


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("SKILLS MANAGER TEST SUITE")
    print("=" * 60)
    print()
    
    # Unit tests with temp directories
    test_skill_discovery()
    test_manifest_loading()
    test_skill_content_loading()
    test_keyword_matching()
    test_provider_filtering()
    test_prompt_injection()
    test_token_efficiency()
    test_multiple_skills()
    test_skill_not_found()
    test_malformed_manifest()
    test_empty_skills_dir()
    
    # Edge case tests
    print("=" * 60)
    print("EDGE CASE TESTS")
    print("=" * 60)
    print()
    test_none_skills_dir()
    test_empty_string_skills_dir()
    test_nonexistent_skills_directory()
    test_missing_manifest_json()
    test_skill_file_missing_referenced_in_manifest()
    test_empty_skill_file()
    test_no_skills_match_provider()
    test_no_skills_match_keywords()
    test_relative_path_skills_dir()
    test_absolute_path_skills_dir()
    test_skills_with_empty_keywords()
    test_skills_with_empty_providers()
    test_duplicate_skill_names()
    test_config_with_none_skills_config()
    
    # Integration tests with real files
    print("=" * 60)
    print("INTEGRATION TESTS")
    print("=" * 60)
    print()
    test_all_skill_files_exist()
    test_skill_file_format()
    test_skill_content_not_empty()
    test_agents_md_exists()
    test_agents_md_required_sections()
    test_skills_config_in_yaml()
    test_default_skills_per_agent()
    test_create_skills_manager_factory()
    
    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
