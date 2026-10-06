"""Command line interface: python -m a11ylint <file-or-folder> ..."""
import argparse
import sys
from pathlib import Path

from a11ylint.checker import RULES, check_source
from a11ylint.report import counts, format_json, format_text

HTML_SUFFIXES = {".html", ".htm"}


def collect_files(paths):
    files = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in HTML_SUFFIXES))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def build_parser():
    parser = argparse.ArgumentParser(
        prog="a11ylint", description="Check HTML files for common WCAG 2.1 accessibility problems.")
    parser.add_argument("paths", nargs="*", help="HTML files or folders to check")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on", choices=["error", "warning", "never"], default="error",
                        help="when to exit with code 1 (default: error)")
    parser.add_argument("--list-rules", action="store_true", help="show all rules and exit")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.list_rules:
        for rule, (wcag, severity, description) in RULES.items():
            print(f"{rule:<18} WCAG {wcag:<6} {severity:<8} {description}")
        return 0
    if not args.paths:
        print("error: give at least one HTML file or folder", file=sys.stderr)
        return 2
    try:
        files = collect_files(args.paths)
    except FileNotFoundError as exc:
        print(f"error: path not found: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("error: no .html or .htm files found", file=sys.stderr)
        return 2

    results = []
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        results.append((path, check_source(source)))

    print(format_json(results) if args.format == "json" else format_text(results))
    errors, warnings = counts(results)
    if args.fail_on == "error" and errors:
        return 1
    if args.fail_on == "warning" and (errors or warnings):
        return 1
    return 0
