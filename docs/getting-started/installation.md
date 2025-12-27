# Installation

## Requirements

- **Python 3.13+** - depswiz requires Python 3.13 or higher
- **pip** or **uv** - For package installation

## Installation Methods

### Using pip

```bash
pip install depswiz
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver:

```bash
uv add depswiz
```

Or install globally:

```bash
uv tool install depswiz
```

### From Source

For the latest development version:

```bash
git clone https://github.com/moinsen-dev/depswiz.git
cd depswiz
pip install -e .
```

Or with uv:

```bash
git clone https://github.com/moinsen-dev/depswiz.git
cd depswiz
uv sync
```

## Verify Installation

After installation, verify depswiz is working:

```bash
depswiz --version
```

You should see output like:

```
depswiz 0.2.0
```

## Optional Dependencies

### Claude Code (for AI features)

To use the `depswiz suggest` command and `--upgrade` features, install [Claude Code](https://claude.ai/code):

```bash
# macOS
brew install claude-code

# Or via npm
npm install -g @anthropic-ai/claude-code
```

Verify Claude Code is installed:

```bash
claude --version
```

## Shell Completion

depswiz supports shell completion for bash, zsh, and fish.

### Bash

```bash
# Add to ~/.bashrc
eval "$(_DEPSWIZ_COMPLETE=bash_source depswiz)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_DEPSWIZ_COMPLETE=zsh_source depswiz)"
```

### Fish

```bash
# Add to ~/.config/fish/completions/depswiz.fish
_DEPSWIZ_COMPLETE=fish_source depswiz > ~/.config/fish/completions/depswiz.fish
```

## Upgrading

### pip

```bash
pip install --upgrade depswiz
```

### uv

```bash
uv add --upgrade depswiz
```

## Uninstalling

### pip

```bash
pip uninstall depswiz
```

### uv

```bash
uv remove depswiz
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started with basic commands
- [Configuration](../configuration.md) - Customize depswiz behavior
