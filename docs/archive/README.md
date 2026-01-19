# AXE Documentation Archive

This directory contains historical documentation, implementation summaries, and past reports. These documents provide context for the project's evolution and development history.

## Archive Contents

### Implementation Summaries (`implementation-summaries/`)

Historical documentation of features and bug fixes implemented in AXE:

**Core Feature Implementations:**
- Skills system implementation
- Sandbox integration (Bubblewrap)
- Anthropic API integration
- Multi-format parser (XML, Bash, Markdown)
- Silent builds system
- Dynamic token management
- Minifier implementation

**Bug Fixes & Improvements:**
- Absolute path fix
- Database location fix
- Duplicate execution fix
- Heredoc execution fix
- Task completion fix
- Collab tool syntax fix
- Shell operator support

**Other Summaries:**
- Before/after comparisons
- Refactoring notes
- Implementation completion reports
- Model configuration guides

### PR Reports (`pr-reports/`)

Pull request validation reports and executive summaries:
- PR #23 validation report
- PR #23 executive summary

## Purpose of Archive

These documents are preserved for:

1. **Historical Context** - Understanding how features evolved
2. **Development Insights** - Learning from past decisions
3. **Reference Material** - Looking up implementation details
4. **Onboarding** - Helping new contributors understand the codebase history
5. **Debugging** - Finding when and how bugs were fixed

## Archive Organization

```
archive/
├── README.md (this file)
├── implementation-summaries/
│   ├── Core features
│   ├── Bug fixes
│   ├── Improvements
│   └── Technical reports
└── pr-reports/
    └── Pull request summaries
```

## When to Use Archive

**Use archived documentation when you need to:**
- Understand why a design decision was made
- Find details about a specific implementation
- Look up when a bug was fixed
- Research past PR discussions
- Trace feature evolution

**For current information, use:**
- [../README.md](../README.md) - Documentation hub
- [../features/](../features/) - Current feature docs
- [../references/](../references/) - Quick references
- [../../ARCHITECTURE.md](../../ARCHITECTURE.md) - Current architecture
- [../../README.md](../../README.md) - Project overview

## Archive vs. Active Documentation

| Type | Location | Purpose | Maintenance |
|------|----------|---------|-------------|
| **Active Docs** | `docs/features/`, `docs/references/` | Current usage guides | Regularly updated |
| **Architecture** | `ARCHITECTURE.md` | System design | Updated with changes |
| **Archive** | `docs/archive/` | Historical record | Rarely updated |

## Contributing to Archive

### Adding to Archive

When archiving documentation:
1. Ensure the document is truly historical (superseded by newer docs)
2. Place in appropriate subdirectory
3. Do not modify archived content (preserve history)
4. Add entry to this README if significant

### Do NOT Archive

- Active feature documentation
- Current quick references
- Up-to-date security reports
- Actively maintained guides

## Implementation Summaries Index

For a complete list of implementation summaries, see:
```bash
ls implementation-summaries/
```

Key summaries include:
- `ANTHROPIC_IMPLEMENTATION_SUMMARY.md` - Anthropic Claude integration
- `SKILLS_SYSTEM_IMPLEMENTATION_SUMMARY.md` - Agent skills system
- `SANDBOX_IMPLEMENTATION_SUMMARY.md` - Sandboxed execution
- `XML_PARSER_IMPLEMENTATION.md` - XML parser implementation
- `MULTI_FORMAT_PARSER_IMPLEMENTATION.md` - Multi-format parsing

## PR Reports Index

For a complete list of PR reports, see:
```bash
ls pr-reports/
```

---

For the complete documentation index, see [../README.md](../README.md)
