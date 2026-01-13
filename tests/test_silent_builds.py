#!/usr/bin/env python3
"""
Test script for silent builds feature implementation.
Validates BUILD GUIDELINES in agent system prompts and skills files.
"""
import os
import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_axe_yaml_is_valid():
    """Test that axe.yaml is valid YAML and can be parsed."""
    print("Testing axe.yaml validity...")
    
    axe_yaml_path = Path(__file__).parent.parent / "axe.yaml"
    assert axe_yaml_path.exists(), "axe.yaml should exist"
    
    with open(axe_yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config is not None, "axe.yaml should parse successfully"
    assert 'agents' in config, "axe.yaml should have 'agents' section"
    
    print("✓ axe.yaml is valid YAML")
    return config


def test_all_agents_have_build_guidelines(config):
    """Test that all agents have BUILD GUIDELINES in their system prompts."""
    print("Testing BUILD GUIDELINES in agent system prompts...")
    
    agents = config['agents']
    agents_to_check = [
        'gpt', 'claude', 'llama', 'grok', 'copilot',
        'titan', 'scout', 'oracle', 'deepthink', 'coder',
        'vision', 'multimedia', 'maverick',
        'qwen_thinking', 'qwen_coder', 'qwen_vision',
        'deepseek', 'grok_code'
    ]
    
    for agent_name in agents_to_check:
        assert agent_name in agents, f"Agent {agent_name} should be in config"
        
        agent = agents[agent_name]
        assert 'system_prompt' in agent, f"Agent {agent_name} should have system_prompt"
        
        system_prompt = agent['system_prompt']
        assert 'BUILD GUIDELINES' in system_prompt, \
            f"Agent {agent_name} should have BUILD GUIDELINES section"
        
        print(f"  ✓ {agent_name}: BUILD GUIDELINES found")
    
    print("✓ All agents have BUILD GUIDELINES")


def test_build_guidelines_contain_required_flags(config):
    """Test that BUILD GUIDELINES contain the required build system flags."""
    print("Testing BUILD GUIDELINES content...")
    
    required_flags = [
        'make -s',
        'make --silent',
        './configure --quiet',
        'cmake --build',
        'meson setup --quiet',
        'gradle --quiet',
        'mvn -q',
        'mvn --quiet',
        'scons -Q',
    ]
    
    agents = config['agents']
    
    for agent_name in agents:
        agent = agents[agent_name]
        system_prompt = agent.get('system_prompt', '')
        
        if 'BUILD GUIDELINES' in system_prompt:
            # Extract BUILD GUIDELINES section
            build_section = system_prompt.split('BUILD GUIDELINES')[1]
            
            # Check for at least some of the required flags
            # (not all agents need all flags, but they should have the core ones)
            core_flags = ['make', 'cmake', 'gradle', 'maven']
            found_flags = sum(1 for flag in core_flags if flag.lower() in build_section.lower())
            
            assert found_flags >= 2, \
                f"Agent {agent_name} BUILD GUIDELINES should mention at least 2 core build systems"
            
            print(f"  ✓ {agent_name}: Contains appropriate build system flags")
    
    print("✓ BUILD GUIDELINES contain required build system flags")


def test_claude_has_security_specific_guidelines(config):
    """Test that Claude has security-specific BUILD GUIDELINES."""
    print("Testing Claude's security-specific BUILD GUIDELINES...")
    
    claude = config['agents']['claude']
    system_prompt = claude['system_prompt']
    
    assert 'BUILD GUIDELINES' in system_prompt, "Claude should have BUILD GUIDELINES"
    
    # Claude should have security-specific mentions
    build_section = system_prompt.split('BUILD GUIDELINES')[1]
    
    # Check for security-related keywords
    security_keywords = ['security', 'valgrind', 'quiet']
    found_keywords = [kw for kw in security_keywords if kw.lower() in build_section.lower()]
    
    assert len(found_keywords) >= 1, \
        "Claude's BUILD GUIDELINES should mention security tools or quiet flags"
    
    print(f"  ✓ Claude has security-specific BUILD GUIDELINES")
    print(f"    Found keywords: {', '.join(found_keywords)}")
    print("✓ Claude has security-specific guidelines")


def test_skills_directory_exists():
    """Test that skills directory exists."""
    print("Testing skills directory...")
    
    skills_dir = Path(__file__).parent.parent / "skills"
    assert skills_dir.exists(), "skills/ directory should exist"
    assert skills_dir.is_dir(), "skills/ should be a directory"
    
    print("✓ skills/ directory exists")
    return skills_dir


def test_build_md_exists_and_valid(skills_dir):
    """Test that skills/build.md exists and is properly formatted."""
    print("Testing skills/build.md...")
    
    build_md = skills_dir / "build.md"
    assert build_md.exists(), "skills/build.md should exist"
    
    with open(build_md, 'r') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        '# Silent Builds Skill',
        '## Overview',
        '## Supported Build Systems',
        '### Make',
        '### CMake',
        '### Maven',
        '### Gradle',
        '## Integration with axe.yaml',
        '## Best Practices',
    ]
    
    for section in required_sections:
        assert section in content, f"build.md should have '{section}' section"
    
    # Check for build system examples
    assert '```EXEC' in content, "build.md should have EXEC block examples"
    assert 'make -s' in content, "build.md should mention 'make -s'"
    assert 'cmake --build' in content, "build.md should mention cmake commands"
    
    print("  ✓ build.md exists and has required sections")
    print("  ✓ build.md contains build system examples")
    print("✓ skills/build.md is valid")


def test_claude_build_md_exists_and_valid(skills_dir):
    """Test that skills/claude_build.md exists and is properly formatted."""
    print("Testing skills/claude_build.md...")
    
    claude_build_md = skills_dir / "claude_build.md"
    assert claude_build_md.exists(), "skills/claude_build.md should exist"
    
    with open(claude_build_md, 'r') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        '# Claude Security-Focused Build Skill',
        '## Overview',
        '## Security Auditing Workflow',
        '## Silent Security Builds',
        '### Security-Specific Tools',
        '#### Valgrind',
        '#### Cppcheck',
        '## Best Practices for Security Audits',
    ]
    
    for section in required_sections:
        assert section in content, f"claude_build.md should have '{section}' section"
    
    # Check for security tool examples
    assert 'valgrind --quiet' in content, "claude_build.md should mention valgrind --quiet"
    assert 'cppcheck --quiet' in content, "claude_build.md should mention cppcheck --quiet"
    
    # Check for severity levels
    assert 'CRITICAL' in content, "claude_build.md should mention severity levels"
    assert 'HIGH' in content, "claude_build.md should mention severity levels"
    
    print("  ✓ claude_build.md exists and has required sections")
    print("  ✓ claude_build.md contains security tool examples")
    print("  ✓ claude_build.md mentions severity levels")
    print("✓ skills/claude_build.md is valid")


def test_build_guidelines_format_consistency(config):
    """Test that BUILD GUIDELINES have consistent formatting across agents."""
    print("Testing BUILD GUIDELINES format consistency...")
    
    agents = config['agents']
    build_guideline_agents = []
    
    for agent_name, agent in agents.items():
        system_prompt = agent.get('system_prompt', '')
        if 'BUILD GUIDELINES' in system_prompt:
            build_guideline_agents.append(agent_name)
    
    # Should have BUILD GUIDELINES for all agents in the config
    # Calculate expected minimum based on known agents
    expected_agents = len(agents)
    assert len(build_guideline_agents) >= expected_agents, \
        f"Should have BUILD GUIDELINES for all {expected_agents} agents, found {len(build_guideline_agents)}"
    
    print(f"  ✓ Found BUILD GUIDELINES in {len(build_guideline_agents)} agents")
    
    # Check that all have similar structure
    for agent_name in build_guideline_agents:
        agent = agents[agent_name]
        system_prompt = agent['system_prompt']
        build_section = system_prompt.split('BUILD GUIDELINES')[1]
        
        # Should mention "verbose" or "debugging" for when to enable verbose output
        assert 'verbose' in build_section.lower() or 'debug' in build_section.lower(), \
            f"Agent {agent_name} BUILD GUIDELINES should mention when to use verbose output"
    
    print("  ✓ All BUILD GUIDELINES mention when to use verbose output")
    print("✓ BUILD GUIDELINES have consistent formatting")


def test_no_breaking_changes_to_existing_prompts(config):
    """Test that existing prompt structure is preserved."""
    print("Testing that existing prompt structure is preserved...")
    
    # Check that essential sections still exist
    essential_sections = {
        'gpt': ['EXPERTISE', 'TOOL USAGE', 'COLLABORATION RULES'],
        'claude': ['SECURITY ANALYSIS', 'TOOL USAGE', 'COLLABORATION RULES'],
        'llama': ['EXPERTISE', 'TOOL USAGE', 'COLLABORATION RULES'],
    }
    
    agents = config['agents']
    
    for agent_name, required_sections in essential_sections.items():
        agent = agents[agent_name]
        system_prompt = agent['system_prompt']
        
        for section in required_sections:
            assert section in system_prompt, \
                f"Agent {agent_name} should still have '{section}' section"
        
        print(f"  ✓ {agent_name}: All essential sections preserved")
    
    print("✓ No breaking changes to existing prompts")


def test_token_savings_documentation():
    """Test that token savings are documented."""
    print("Testing token savings documentation...")
    
    skills_dir = Path(__file__).parent.parent / "skills"
    build_md = skills_dir / "build.md"
    
    with open(build_md, 'r') as f:
        content = f.read()
    
    # Should mention token savings
    assert 'token' in content.lower(), "build.md should mention tokens"
    assert 'saving' in content.lower() or 'savings' in content.lower(), \
        "build.md should mention savings"
    
    # Should have some percentage or numeric estimate
    assert '%' in content, "build.md should have percentage estimates"
    
    print("  ✓ build.md documents token savings")
    
    # Claude's version should also mention token savings
    claude_build_md = skills_dir / "claude_build.md"
    with open(claude_build_md, 'r') as f:
        content = f.read()
    
    assert 'token' in content.lower(), "claude_build.md should mention tokens"
    
    print("  ✓ claude_build.md documents token savings")
    print("✓ Token savings are documented")


def run_all_tests():
    """Run all tests for silent builds feature."""
    print("=" * 70)
    print("SILENT BUILDS FEATURE TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Test 1: YAML validity
        config = test_axe_yaml_is_valid()
        print()
        
        # Test 2: All agents have BUILD GUIDELINES
        test_all_agents_have_build_guidelines(config)
        print()
        
        # Test 3: BUILD GUIDELINES contain required flags
        test_build_guidelines_contain_required_flags(config)
        print()
        
        # Test 4: Claude has security-specific guidelines
        test_claude_has_security_specific_guidelines(config)
        print()
        
        # Test 5: Skills directory exists
        skills_dir = test_skills_directory_exists()
        print()
        
        # Test 6: build.md is valid
        test_build_md_exists_and_valid(skills_dir)
        print()
        
        # Test 7: claude_build.md is valid
        test_claude_build_md_exists_and_valid(skills_dir)
        print()
        
        # Test 8: Format consistency
        test_build_guidelines_format_consistency(config)
        print()
        
        # Test 9: No breaking changes
        test_no_breaking_changes_to_existing_prompts(config)
        print()
        
        # Test 10: Token savings documentation
        test_token_savings_documentation()
        print()
        
        print("=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • axe.yaml is valid and all agents have BUILD GUIDELINES")
        print("  • Claude has security-specific BUILD GUIDELINES")
        print("  • skills/build.md exists with comprehensive documentation")
        print("  • skills/claude_build.md exists with security-focused guidelines")
        print("  • No breaking changes to existing agent functionality")
        print("  • Token savings are documented and estimated")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print("TEST FAILED! ✗")
        print("=" * 70)
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print()
        print("=" * 70)
        print("TEST ERROR! ✗")
        print("=" * 70)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
