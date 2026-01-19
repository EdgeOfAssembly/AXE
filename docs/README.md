# AXE Documentation

```
   ___   _  __ ____
  / _ | | |/_// __/
 / __ |_>  < / _/  
/_/ |_/_/|_|/___/  

   Documentation Hub
```

Welcome to the AXE documentation! This directory contains comprehensive guides, references, and technical documentation for the AXE Agent eXecution Engine.

## 📚 Documentation Index

### Core Documentation
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture, module structure, and data flow diagrams
- **[api-providers.md](api-providers.md)** - Detailed API provider documentation (Anthropic, OpenAI, xAI, HuggingFace, GitHub)
- **[security.md](security.md)** - Security audit results and best practices

### Features
> Detailed feature documentation and guides

- **[features/sandbox.md](features/sandbox.md)** - Bubblewrap sandboxed command execution
- **[features/write-blocks.md](features/write-blocks.md)** - File manipulation and code blocks
- **[features/parsers.md](features/parsers.md)** - Multi-format tool call parsing (XML, Bash, Markdown)
- **[features/README.md](features/README.md)** - Complete features overview

### References
> Quick references and cheat sheets

- **[references/quick-reference.md](references/quick-reference.md)** - Commands, shortcuts, and common patterns
- **[references/README.md](references/README.md)** - Reference materials index

### Workshop Tools
> Dynamic analysis and security tools

- **[workshop/quick-reference.md](workshop/quick-reference.md)** - Workshop tools guide (Chisel, Hammer, Saw, Plane)
- **[workshop/benchmarks.md](workshop/benchmarks.md)** - Performance benchmarks
- **[workshop/security-audit.md](workshop/security-audit.md)** - Security audit results
- **[workshop/dependency-validation.md](workshop/dependency-validation.md)** - Dependency validation reports
- **[workshop/test-results.md](workshop/test-results.md)** - Test suite results
- **[workshop/README.md](workshop/README.md)** - Workshop overview

### Archive
> Historical documentation and implementation summaries

- **[archive/README.md](archive/README.md)** - Archive contents and organization
- **[archive/implementation-summaries/](archive/implementation-summaries/)** - Feature implementation summaries
- **[archive/pr-reports/](archive/pr-reports/)** - Pull request validation reports

### Diagrams
> Visual representations of system architecture

- **[diagrams/README.md](diagrams/README.md)** - Architecture diagrams and visual documentation

## 🚀 Quick Start

New to AXE? Start here:

1. **[README.md](../README.md)** - Project overview and installation
2. **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Understand the system design
3. **[features/README.md](features/README.md)** - Explore available features
4. **[references/quick-reference.md](references/quick-reference.md)** - Common commands and patterns

## 🔍 Finding What You Need

### I want to...

**Understand how AXE works**
→ Read [ARCHITECTURE.md](../ARCHITECTURE.md) for system design and data flow

**Use a specific AI provider**
→ See [api-providers.md](api-providers.md) for setup and configuration

**Run commands safely**
→ Check [features/sandbox.md](features/sandbox.md) for sandboxed execution

**Parse different tool formats**
→ Review [features/parsers.md](features/parsers.md) for supported formats

**Use Workshop tools**
→ Start with [workshop/quick-reference.md](workshop/quick-reference.md)

**Find command syntax**
→ Reference [references/quick-reference.md](references/quick-reference.md)

**Review security measures**
→ See [security.md](security.md) for audit results

**Look up historical implementations**
→ Browse [archive/](archive/) for past summaries and reports

## 📖 Additional Resources

### Project Files (Root Directory)
- **[AGENTS.md](../AGENTS.md)** - AI agent collaboration standard
- **[MISSION.md](../MISSION.md)** - Project philosophy and goals
- **[LICENSE](../LICENSE)** - Project license

### Configuration
- **[axe.yaml](../axe.yaml)** - Main configuration file
- **[models.yaml](../models.yaml)** - Model metadata and capabilities
- **[skills/manifest.json](../skills/manifest.json)** - Agent skills registry

## 🤝 Contributing

When adding new documentation:

1. Place in the appropriate subdirectory (features, references, workshop, or archive)
2. Use lowercase-kebab-case for filenames
3. Update this README.md with a link to your new documentation
4. Add internal navigation links where appropriate
5. Follow existing documentation style and formatting

## 📝 Documentation Standards

- Use Markdown for all documentation
- Include code examples where relevant
- Add clear section headers for navigation
- Cross-reference related documents
- Keep examples tested and up-to-date
- Use ASCII art sparingly for visual clarity

---

**Need help?** Check the [references/quick-reference.md](references/quick-reference.md) or explore the subdirectories above.
