"""Command-line interface for k8s-version-looker."""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .client import get_cluster_versions
from .formatters import generate_html, generate_json, generate_markdown, display_text

__version__ = "0.1.0"


def progress_indicator(completed: int, total: int, context_name: str) -> None:
    """Display progress as clusters are queried."""
    # Clear line and show progress
    percentage = int((completed / total) * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * completed / total) if total > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)

    sys.stderr.write(f"\r\033[KQuerying clusters: [{bar}] {completed}/{total} ({percentage}%) - {context_name}")
    sys.stderr.flush()

    # Add newline when complete
    if completed == total:
        sys.stderr.write("\n")
        sys.stderr.flush()


def validate_output_file(file_path: str) -> None:
    """Validate output file path and permissions."""
    path = Path(file_path)

    # Check if parent directory exists, create if not
    parent = path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot create directory {parent}: {e}")

    # Check write permissions on parent directory
    if not os.access(parent, os.W_OK):
        raise ValueError(f"No write permission for directory {parent}")

    # Check if file exists and is writable
    if path.exists() and not os.access(path, os.W_OK):
        raise ValueError(f"No write permission for file {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Kubernetes cluster versions and node information")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-c", "--context", help="Check the version of a specific context only")
    parser.add_argument("-k", "--insecure", action="store_true", help="Skip TLS certificate verification")
    parser.add_argument("-o", "--output", choices=["text", "html", "markdown", "json"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("-f", "--output-file", help="Save output to a file")
    parser.add_argument("-t", "--timeout", type=int, default=5,
                        help="Timeout for cluster queries in seconds (default: 5)")
    parser.add_argument("--include", help="Include only contexts matching these patterns (comma-separated globs)")
    parser.add_argument("--exclude", help="Exclude contexts matching these patterns (comma-separated globs)")
    parser.add_argument("-d", "--detailed", action="store_true",
                        help="Show detailed patch versions (default: group by minor version)")
    args = parser.parse_args()

    # Validate output file path if provided
    if args.output_file:
        try:
            validate_output_file(args.output_file)
        except ValueError as e:
            print(f"Error: {e}")
            return

    # Parse include/exclude patterns
    include_patterns = [p.strip() for p in args.include.split(",")] if args.include else None
    exclude_patterns = [p.strip() for p in args.exclude.split(",")] if args.exclude else None

    # Get cluster version information with progress indicator
    try:
        versions = get_cluster_versions(
            specific_context=args.context,
            skip_tls_verify=args.insecure,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            timeout=args.timeout,
            progress_callback=progress_indicator
        )
    except KeyboardInterrupt:
        sys.stderr.write("\n\n⚠️  Interrupted. Exiting...\n")
        sys.exit(130)  # Standard exit code for Ctrl+C

    # Handle different output formats
    try:
        if args.output == "text":
            display_text(versions, detailed=args.detailed)
        elif args.output == "html":
            html_content = generate_html(versions, args.output_file, detailed=args.detailed)
            if not args.output_file:
                print(html_content)
        elif args.output == "markdown":
            md_content = generate_markdown(versions, args.output_file, detailed=args.detailed)
            if not args.output_file:
                print(md_content)
        elif args.output == "json":
            json_content = generate_json(versions, args.output_file, detailed=args.detailed)
            if not args.output_file:
                print(json_content)
    except KeyboardInterrupt:
        sys.stderr.write("\n\n⚠️  Interrupted. Exiting...\n")
        sys.exit(130)


if __name__ == "__main__":
    main()
