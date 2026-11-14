#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Data Quality Report

Highlights repositories that are missing the metadata which makes a solution
discoverable and reusable (description, licence, topics, language, contact).

This is a reporting tool, not a gate: it always exits 0 unless the data file
cannot be read, so it can run in CI to surface trends without blocking work.

Usage:
    python scripts/data_quality_report.py            # human readable
    python scripts/data_quality_report.py --markdown # GitHub step summary
    python scripts/data_quality_report.py --json     # machine readable
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_DATA_FILE = 'data/repositories.json'

# Repositories missing these fields are harder to find and reuse.
CHECKS = {
    'missing_description': lambda r: not (r.get('description') or '').strip(),
    'missing_licence': lambda r: not r.get('license'),
    'missing_topics': lambda r: not r.get('topics'),
    'missing_language': lambda r: not r.get('language'),
    'missing_contact': lambda r: not (r.get('solution_metadata') or {}).get('contact'),
    'archived': lambda r: bool(r.get('archived')),
}

CHECK_LABELS = {
    'missing_description': 'No description',
    'missing_licence': 'No licence',
    'missing_topics': 'No topics',
    'missing_language': 'No primary language',
    'missing_contact': 'No contact in solution.yml',
    'archived': 'Archived',
}


def load_repositories(path):
    """Load the published repository data."""
    with open(path, 'r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f'{path} should contain a list of repositories')
    return data


def build_report(repositories):
    """Summarise metadata completeness across all repositories."""
    total = len(repositories)
    counts = {name: 0 for name in CHECKS}
    offenders = {name: [] for name in CHECKS}

    for repo in repositories:
        name = repo.get('full_name') or repo.get('name') or 'unknown'
        for check_name, predicate in CHECKS.items():
            if predicate(repo):
                counts[check_name] += 1
                offenders[check_name].append(name)

    complete = sum(
        1 for repo in repositories
        if not any(
            CHECKS[check](repo)
            for check in ('missing_description', 'missing_licence', 'missing_topics')
        )
    )

    return {
        'total_repositories': total,
        'fully_described': complete,
        'fully_described_percentage': round((complete / total) * 100, 1) if total else 0.0,
        'counts': counts,
        'percentages': {
            name: round((count / total) * 100, 1) if total else 0.0
            for name, count in counts.items()
        },
        'offenders': offenders,
    }


def format_text(report, limit):
    """Render the report for a terminal."""
    lines = [
        'NHS Wales Solutions Exchange - Data Quality Report',
        '=' * 50,
        f"Total repositories: {report['total_repositories']}",
        f"Fully described (description + licence + topics): "
        f"{report['fully_described']} ({report['fully_described_percentage']}%)",
        '',
    ]
    for name, count in report['counts'].items():
        lines.append(f"{CHECK_LABELS[name]}: {count} ({report['percentages'][name]}%)")
        for repo_name in report['offenders'][name][:limit]:
            lines.append(f"    - {repo_name}")
        remaining = count - limit
        if remaining > 0:
            lines.append(f"    ... and {remaining} more")
        lines.append('')
    return '\n'.join(lines)


def format_markdown(report, limit):
    """Render the report as Markdown for a GitHub step summary."""
    lines = [
        '## 🔎 Solutions Exchange data quality',
        '',
        f"**{report['total_repositories']}** repositories published. "
        f"**{report['fully_described']}** ({report['fully_described_percentage']}%) "
        'have a description, licence and topics.',
        '',
        '| Check | Repositories | Share |',
        '| --- | ---: | ---: |',
    ]
    for name, count in report['counts'].items():
        lines.append(f"| {CHECK_LABELS[name]} | {count} | {report['percentages'][name]}% |")

    lines.append('')
    for name, count in report['counts'].items():
        if not count:
            continue
        lines.append(f"<details><summary>{CHECK_LABELS[name]} ({count})</summary>")
        lines.append('')
        for repo_name in report['offenders'][name][:limit]:
            lines.append(f"- {repo_name}")
        remaining = count - limit
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")
        lines.append('')
        lines.append('</details>')
        lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-file', default=DEFAULT_DATA_FILE,
                        help=f'Path to repository data (default: {DEFAULT_DATA_FILE})')
    parser.add_argument('--limit', type=int, default=10,
                        help='Maximum repositories listed per check (default: 10)')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--markdown', action='store_true', help='Output Markdown')
    output.add_argument('--json', action='store_true', help='Output JSON')
    args = parser.parse_args()

    try:
        repositories = load_repositories(args.data_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'Unable to read {args.data_file}: {exc}', file=sys.stderr)
        return 1

    report = build_report(repositories)

    if args.json:
        print(json.dumps(report, indent=2))
    elif args.markdown:
        print(format_markdown(report, args.limit))
    else:
        print(format_text(report, args.limit))

    return 0


if __name__ == '__main__':
    sys.exit(main())
