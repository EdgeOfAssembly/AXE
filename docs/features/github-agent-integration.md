# GitHub Agent Integration

## Overview

Allows agents in collaborative sessions to autonomously push code to GitHub with **mandatory human review**.

## Safety Features

- ✅ **Disabled by default** - Must explicitly enable
- ✅ **Human review required** - Cannot be bypassed
- ✅ **SSH-based** - Uses existing credentials
- ✅ **No auto-merge** - Human controls PR merging
- ✅ **Easy to disable** - Single flag

## Usage

```bash
# Enable GitHub mode
python axe.py --collab llama,claude \
  --workspace . \
  --time 60 \
  --task "Add error handling" \
  --enable-github
```

## Agent Usage

Agents signal they're ready to push:

```
[claude] All tests pass. Ready to push.
[claude] [[GITHUB_READY: agent/add-error-handling, Add comprehensive error handling]]
```

This triggers an **automatic pause** for human review.

## Review Interface

```
🚨 AGENTS READY TO PUSH TO GITHUB
════════════════════════════════════════════

Branch: agent/add-error-handling
Commit: Add comprehensive error handling

Files changed:
  M src/parser.c
  M tests/test_parser.c

Options:
  'a' - Approve and push
  'r' - Reject and give feedback
  'd' - Show full diff
  's' - Skip, end session

Choice: 
```

## Configuration

In `axe.yaml`:

```yaml
github_integration:
  enabled: false  # Must explicitly enable
  require_review: true  # Cannot be disabled (safety)
  branch_prefix: agent/
  ssh_key_path: null  # Auto-detect
```

## Command Line Option

```bash
--enable-github     Enable autonomous GitHub operations (disabled by default)
```

## Token Format

Agents use the following token to signal readiness:

```
[[GITHUB_READY: branch-name, commit message]]
```

Example:
```
[[GITHUB_READY: agent/fix-bug, Fix memory leak in parser]]
```

## Review Flow

1. **Agent signals ready**: Uses `[[GITHUB_READY: ...]]` token
2. **Session pauses**: Review interface appears
3. **Human reviews**: Can view diff, approve, or reject
4. **If approved**: Code is pushed to specified branch
5. **Optional PR creation**: Human can create PR via `gh` CLI
6. **If rejected**: Feedback is sent back to agents

## Rejection and Feedback

When rejecting a push request:

1. Enter 'r' at the review prompt
2. Provide feedback explaining why (e.g., "Need more tests")
3. Session resumes with feedback injected
4. Agents can address feedback and signal ready again

## Requirements

- Git repository initialized in workspace
- SSH authentication configured for remote
- (Optional) `gh` CLI for PR creation

## Safety Guarantees

1. **Disabled by default**: Must use `--enable-github` flag
2. **Human review required**: Every push reviewed before execution
3. **No auto-merge**: PRs must be manually merged
4. **SSH-only**: Uses existing SSH credentials, no token storage
5. **Clear warnings**: Visual indicators when enabled

## Removal

To completely remove this feature:

1. Delete `core/github_agent.py`
2. Remove `github_enabled` parameter from `CollaborativeSession.__init__`
3. Remove the GitHub check in `_run_collaboration_loop`
4. Remove `--enable-github` argument from main()
5. Remove GitHub methods from CollaborativeSession

**Zero impact on existing functionality when disabled.**

## Example Session

```bash
$ python axe.py --collab llama,claude \
    --workspace ~/myproject \
    --task "Add logging" \
    --enable-github

✓ GitHub agent mode enabled

[Starting collaborative session...]

[llama] I'll add a logging module...
[EXEC: touch logger.py]
[WRITE: logger.py]

[claude] Looks good. Tests pass. Ready to commit.
[claude] [[GITHUB_READY: agent/add-logging, Add structured logging module]]

🚨 AGENTS READY TO PUSH TO GITHUB
════════════════════════════════════════════

Branch: agent/add-logging
Commit: Add structured logging module

Files changed:
  M logger.py
  M tests/test_logger.py

Options:
  'a' - Approve and push
  'r' - Reject and give feedback
  'd' - Show full diff
  's' - Skip, end session

Choice: a

✓ Pushing to GitHub...
✓ Pushed to branch: agent/add-logging
Create PR? (y/n): y
✓ PR created: https://github.com/user/repo/pull/123

SESSION ENDED
```

## Error Handling

The GitHub agent handles errors gracefully:

- **No git repo**: Warning displayed, feature disabled
- **SSH not configured**: Push fails with clear error
- **No changes**: Commit fails with "nothing to commit" message
- **Push fails**: Error displayed, session can continue

## Security Considerations

- Uses existing SSH credentials (no token storage)
- Never bypasses human review
- No automatic PR merging
- Clear visual indicators when enabled
- Can be completely disabled

## Testing

Run tests with:

```bash
python tests/test_github_agent.py
```

Tests cover:
- Disabled by default behavior
- Git repository detection
- Token detection and parsing
- No-op behavior when disabled
- Diff generation
- Error handling
