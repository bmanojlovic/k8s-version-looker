# Kubernetes Version Looker

A tool to check Kubernetes cluster versions and node information from your kubeconfig.

## Features

- Displays Kubernetes cluster version information
- Summarizes node versions by grouping nodes with the same kubelet version
- Shows node counts for each version group along with OS and container runtime information
- Supports multiple output formats: text, HTML, Markdown, and JSON

## Options

- `-v, --version`: Show version and exit
- `-c, --context <context-name>`: Check the version of a specific context only
- `-k, --insecure`: Skip TLS certificate verification (use when having SSL certificate issues)
- `-o, --output <format>`: Output format (text, html, markdown, json)
- `-f, --output-file <filename>`: Save output to a file
- `-t, --timeout <seconds>`: Timeout for cluster queries in seconds (default: 5)
- `--include <patterns>`: Include only contexts matching these patterns (comma-separated globs)
- `--exclude <patterns>`: Exclude contexts matching these patterns (comma-separated globs)

## Examples

```bash
# Default text output to console
python -m k8s_version_looker.main

# Check a specific context (short flag)
python -m k8s_version_looker.main -c my-cluster

# Skip TLS verification (short flag)
python -m k8s_version_looker.main -k

# Generate HTML report (short flags)
python -m k8s_version_looker.main -o html -f report.html

# Generate Markdown report
python -m k8s_version_looker.main --output markdown --output-file report.md

# Generate JSON output (mixed flags)
python -m k8s_version_looker.main -o json -f report.json

# Filter contexts - only production clusters
python -m k8s_version_looker.main --include "prod-*"

# Exclude development and test clusters
python -m k8s_version_looker.main --exclude "dev-*,test-*"

# Combine include and exclude
python -m k8s_version_looker.main --include "prod-*" --exclude "*-backup"

# Increase timeout for slow clusters
python -m k8s_version_looker.main -t 10

# Fast queries with short timeout
python -m k8s_version_looker.main -t 3
```

## Features

- **Parallel Processing**: Queries multiple clusters concurrently for faster results
- **Fast Failure**: Configurable timeouts (default: 5s) with zero retries - fails fast instead of hanging
- **Progress Indicators**: Real-time progress bar showing which cluster is being queried
- **Context Filtering**: Include/exclude clusters using glob patterns
- **Multiple Output Formats**: Text, HTML, Markdown, and JSON
- **Type-Safe**: Full type hints throughout the codebase
- **Well-Tested**: Comprehensive unit test coverage

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/k8s_version_looker --cov-report=html
```

### Project Structure

```
src/k8s_version_looker/
├── __init__.py
├── main.py          # CLI interface
├── client.py        # Kubernetes API client
├── formatters.py    # Output generators
└── models.py        # Data models
```
