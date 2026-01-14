#!/usr/bin/env python3
"""
Demonstration of the Agent Skills System.
Shows how skills are auto-discovered, loaded, and activated based on keywords.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.skills_manager import SkillsManager, create_skills_manager
from utils.formatting import Colors, c


def demo_skill_discovery():
    """Demonstrate skill auto-discovery."""
    print(c("\n=== SKILL DISCOVERY DEMO ===", Colors.CYAN))
    print()
    
    manager = create_skills_manager(skills_dir='skills')
    
    print(f"Discovered {len(manager.skills_cache)} skills:")
    for name, skill in manager.skills_cache.items():
        print(f"  • {name}")
        print(f"    Keywords: {', '.join(skill.keywords[:5])}")
        print(f"    Providers: {', '.join(skill.providers)}")
        print()


def demo_keyword_matching():
    """Demonstrate keyword-based skill activation."""
    print(c("\n=== KEYWORD MATCHING DEMO ===", Colors.CYAN))
    print()
    
    manager = create_skills_manager(skills_dir='skills')
    
    test_prompts = [
        "Analyze this binary for vulnerabilities using angr",
        "Refactor this C++ code to use modern C++20 features",
        "Write a Python script with pytest tests",
        "Disassemble this x86 assembly code",
        "Upgrade this legacy C code to C17",
        "Use IDA Pro to analyze this decompiler output"
    ]
    
    for prompt in test_prompts:
        print(c(f"Prompt: \"{prompt}\"", Colors.YELLOW))
        skills = manager.get_skills_for_task(prompt)
        
        if skills:
            print(c(f"  → Activated skills: {', '.join(s.name for s in skills)}", Colors.GREEN))
        else:
            print(c("  → No skills activated", Colors.RED))
        print()


def demo_provider_filtering():
    """Demonstrate provider-specific skill filtering."""
    print(c("\n=== PROVIDER FILTERING DEMO ===", Colors.CYAN))
    print()
    
    manager = create_skills_manager(skills_dir='skills')
    
    prompt = "Perform security audit on this binary"
    
    providers = ['anthropic', 'openai', 'huggingface']
    
    for provider in providers:
        print(c(f"Provider: {provider}", Colors.YELLOW))
        skills = manager.get_skills_for_task(prompt, provider=provider)
        
        if skills:
            print(c(f"  → Available skills: {', '.join(s.name for s in skills)}", Colors.GREEN))
        else:
            print(c("  → No skills available for this provider", Colors.RED))
        print()


def demo_prompt_injection():
    """Demonstrate skill injection into system prompts."""
    print(c("\n=== PROMPT INJECTION DEMO ===", Colors.CYAN))
    print()
    
    manager = create_skills_manager(skills_dir='skills')
    
    original_prompt = "You are a helpful coding assistant."
    skill = manager.get_skill("python_agent_expert")
    
    if skill:
        enhanced_prompt = manager.inject_skills_to_prompt(original_prompt, [skill])
        
        print(c("Original prompt:", Colors.YELLOW))
        print(f"  {original_prompt}")
        print()
        
        print(c("Enhanced prompt (first 500 chars):", Colors.YELLOW))
        print(f"  {enhanced_prompt[:500]}...")
        print()
        
        # Show token savings estimate
        original_len = len(original_prompt)
        enhanced_len = len(enhanced_prompt)
        added_len = enhanced_len - original_len
        
        print(c(f"Stats:", Colors.CYAN))
        print(f"  Original: {original_len} chars (~{original_len // 4} tokens)")
        print(f"  Enhanced: {enhanced_len} chars (~{enhanced_len // 4} tokens)")
        print(f"  Added: {added_len} chars (~{added_len // 4} tokens)")


def demo_metadata_only():
    """Demonstrate metadata-only loading for token efficiency."""
    print(c("\n=== METADATA-ONLY LOADING DEMO ===", Colors.CYAN))
    print()
    
    manager = create_skills_manager(skills_dir='skills')
    
    skill_name = "reverse_engineering_expert"
    
    # Full skill
    full_skill = manager.get_skill(skill_name)
    print(c(f"Full skill '{skill_name}':", Colors.YELLOW))
    print(f"  Content size: {len(full_skill.content)} chars (~{len(full_skill.content) // 4} tokens)")
    print()
    
    # Metadata only
    metadata = manager.get_skill_metadata_only(skill_name)
    print(c(f"Metadata-only '{skill_name}':", Colors.YELLOW))
    print(f"  Name: {metadata['name']}")
    print(f"  Description: {metadata['description']}")
    print(f"  Keywords: {', '.join(metadata['keywords'][:5])}")
    print(f"  Providers: {', '.join(metadata['providers'])}")
    print()
    
    print(c("Token efficiency:", Colors.CYAN))
    print(f"  Full skill: ~{len(full_skill.content) // 4} tokens")
    print(f"  Metadata only: ~{len(str(metadata)) // 4} tokens")
    print(f"  Savings: ~{(len(full_skill.content) - len(str(metadata))) // 4} tokens")


def demo_agent_integration():
    """Demonstrate integration with agent configuration."""
    print(c("\n=== AGENT INTEGRATION DEMO ===", Colors.CYAN))
    print()
    
    import yaml
    
    # Load agent config
    with open('axe.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    claude_agent = config['agents']['claude']
    default_skills = claude_agent.get('default_skills', [])
    
    print(c(f"Claude agent default skills:", Colors.YELLOW))
    for skill_name in default_skills:
        print(f"  • {skill_name}")
    print()
    
    # Load and display these skills
    manager = create_skills_manager(skills_dir='skills')
    skills = manager.get_skills_by_names(default_skills, provider='anthropic')
    
    print(c(f"Loaded {len(skills)} default skills for Claude:", Colors.GREEN))
    for skill in skills:
        print(f"  • {skill.name}")
        print(f"    Description: {skill.metadata.get('description', 'N/A')}")
        print()


def main():
    """Run all demonstrations."""
    print(c("╔════════════════════════════════════════════════════════════════╗", Colors.CYAN))
    print(c("║        AGENT SKILLS SYSTEM DEMONSTRATION                       ║", Colors.CYAN))
    print(c("╚════════════════════════════════════════════════════════════════╝", Colors.CYAN))
    
    try:
        demo_skill_discovery()
        demo_keyword_matching()
        demo_provider_filtering()
        demo_prompt_injection()
        demo_metadata_only()
        demo_agent_integration()
        
        print(c("\n╔════════════════════════════════════════════════════════════════╗", Colors.GREEN))
        print(c("║           ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY            ║", Colors.GREEN))
        print(c("╚════════════════════════════════════════════════════════════════╝", Colors.GREEN))
        
    except Exception as e:
        print(c(f"\n✗ Error during demonstration: {e}", Colors.RED))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
