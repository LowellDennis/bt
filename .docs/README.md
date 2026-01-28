# BT Documentation

This directory contains developer and user documentation for the BIOS Tool (BT) project.

## Documentation Structure

```
.docs/
  architecture.md    # System architecture and design decisions
  commands.md        # Detailed command reference
  configuration.md   # Configuration system guide
  development.md     # Development setup and workflow
  api/              # API documentation (auto-generated)
```

## Quick Links

- **User Guide**: See main [README.md](../README.md)
- **Changelog**: See [CHANGELOG.md](../CHANGELOG.md)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Copilot Instructions**: See [.github/copilot-instructions.md](../.github/copilot-instructions.md)

## Building Documentation

### API Documentation (Future)
Generate from docstrings:
```bash
sphinx-build -b html .docs/api .docs/api/_build
```

### Documentation Website (Future)
Host on GitHub Pages or ReadTheDocs.

## Documentation Standards

- Use Markdown for all documentation
- Follow Google Style for docstrings
- Include code examples
- Keep examples up-to-date with latest version
- Add screenshots for GUI documentation
