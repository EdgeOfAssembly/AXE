#!/usr/bin/env python3
"""
Validation script for GPT-5.2 Codex Responses API implementation.
This script verifies the configuration is correct without making actual API calls.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.metadata import get_model_info, uses_responses_api, uses_max_completion_tokens
from core.config import Config
from core.agent_manager import AgentManager

def validate_codex_configuration():
    """Validate the full Codex configuration."""
    print("=" * 70)
    print("GPT-5.2 CODEX CONFIGURATION VALIDATION")
    print("=" * 70)
    print()
    
    # 1. Validate model metadata
    print("1. Validating model metadata...")
    model_info = get_model_info('gpt-5.2-codex')
    
    checks = [
        (model_info['context_tokens'] == 192000, "Context tokens: 192,000"),
        (model_info['max_output_tokens'] == 16000, "Max output tokens: 16,000"),
        (model_info.get('api_type') == 'responses', "API type: responses"),
        ('text' in model_info['input_modes'], "Input mode: text"),
        ('function_calling' in model_info['output_modes'], "Output mode: function_calling"),
        (uses_responses_api('gpt-5.2-codex'), "Uses Responses API: True"),
        (uses_max_completion_tokens('gpt-5.2-codex'), "Uses max_completion_tokens: True"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {desc}")
        if not check:
            all_passed = False
    
    if not all_passed:
        print("\n✗ Model metadata validation FAILED")
        return False
    print("  ✓ Model metadata validation passed")
    print()
    
    # 2. Validate agent configuration
    print("2. Validating agent configuration...")
    config = Config()
    agents = config.get('agents', default={})
    
    if 'gpt_codex' not in agents:
        print("  ✗ gpt_codex agent not found in configuration")
        return False
    
    codex_agent = agents['gpt_codex']
    
    checks = [
        (codex_agent['provider'] == 'openai', "Provider: openai"),
        (codex_agent['model'] == 'gpt-5.2-codex', "Model: gpt-5.2-codex"),
        ('codex' in codex_agent.get('alias', []), "Alias includes: codex"),
        ('gptcode' in codex_agent.get('alias', []), "Alias includes: gptcode"),
        (codex_agent.get('api_endpoint') == 'responses', "API endpoint: responses"),
        (codex_agent['context_tokens'] == 192000, "Context tokens: 192,000"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {desc}")
        if not check:
            all_passed = False
    
    if not all_passed:
        print("\n✗ Agent configuration validation FAILED")
        return False
    print("  ✓ Agent configuration validation passed")
    print()
    
    # 3. Validate provider configuration
    print("3. Validating provider configuration...")
    providers = config.get('providers', default={})
    
    if 'openai' not in providers:
        print("  ✗ OpenAI provider not found")
        return False
    
    openai_provider = providers['openai']
    models = openai_provider.get('models', [])
    
    if 'gpt-5.2-codex' not in models:
        print("  ✗ gpt-5.2-codex not in OpenAI provider models list")
        return False
    
    print(f"  ✓ gpt-5.2-codex found in OpenAI provider models list")
    print(f"  ✓ OpenAI provider has {len(models)} models")
    print()
    
    # 4. Validate AgentManager can resolve the agent
    print("4. Validating AgentManager integration...")
    agent_manager = AgentManager(config)
    
    # Test direct name
    resolved = agent_manager.resolve_agent('gpt_codex')
    if not resolved:
        print("  ✗ Failed to resolve 'gpt_codex' agent")
        return False
    print("  ✓ Resolved agent by name: gpt_codex")
    
    # Test aliases
    for alias in ['codex', 'gptcode']:
        resolved = agent_manager.resolve_agent(alias)
        if not resolved:
            print(f"  ✗ Failed to resolve alias: {alias}")
            return False
        print(f"  ✓ Resolved agent by alias: {alias}")
    
    print("  ✓ AgentManager integration validation passed")
    print()
    
    # 5. Validate implementation details
    print("5. Validating implementation details...")
    
    # Check that the Responses API detection logic is correct
    model = 'gpt-5.2-codex'
    uses_responses = uses_responses_api(model) or codex_agent.get('api_endpoint') == 'responses'
    
    if not uses_responses:
        print("  ✗ Responses API detection failed")
        return False
    
    print("  ✓ Responses API detection logic correct")
    print("  ✓ Implementation ready for API calls")
    print()
    
    return True


if __name__ == '__main__':
    print()
    try:
        success = validate_codex_configuration()
        
        if success:
            print("=" * 70)
            print("✅ ALL VALIDATIONS PASSED!")
            print("=" * 70)
            print()
            print("GPT-5.2 Codex is properly configured and ready to use.")
            print()
            print("Usage:")
            print("  - Direct: @gpt_codex")
            print("  - Alias 1: @codex")
            print("  - Alias 2: @gptcode")
            print()
            print("The agent will automatically use the Responses API endpoint")
            print("(/v1/responses) instead of Chat Completions (/v1/chat/completions).")
            print()
            sys.exit(0)
        else:
            print("=" * 70)
            print("❌ VALIDATION FAILED")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
