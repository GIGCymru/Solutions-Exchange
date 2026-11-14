#!/usr/bin/env python3
"""Solution metadata standard for the NHS Wales Solutions Exchange.

Teams describe a solution by committing a ``solution.json`` file to their
repository. The Solutions Exchange pipeline reads that file and attaches the
validated contents to the published record as ``solution_metadata``.

The format is JSON rather than YAML deliberately: it is parseable with the
standard library alone, so the daily data job needs no extra dependency and
the file can be validated in CI without an install step.

Run directly to validate a file:

    python3 scripts/solution_metadata.py path/to/solution.json
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Path looked for inside each repository, in priority order.
METADATA_PATHS = ('solution.json', '.github/solution.json')

# Values accepted for ``lifecycle``.
LIFECYCLE_STAGES = ('idea', 'prototype', 'beta', 'live', 'maintained', 'retired')

# Values accepted for ``support``.
SUPPORT_LEVELS = ('none', 'best-effort', 'supported')

#: field name -> (expected python type, required)
SCHEMA: Dict[str, Tuple[Any, bool]] = {
    'contact': (str, True),
    'organisation': (str, False),
    'lifecycle': (str, False),
    'support': (str, False),
    'summary': (str, False),
    'problem': (str, False),
    'benefits': (list, False),
    'clinical_safety': (str, False),
    'information_governance': (str, False),
    'dependencies': (list, False),
    'reuse_contacts': (list, False),
    'documentation_url': (str, False),
    'demo_url': (str, False),
}

MAX_SUMMARY_LENGTH = 300


def _type_name(expected: Any) -> str:
    return {str: 'string', list: 'list', dict: 'object'}.get(expected, str(expected))


def validate_solution_metadata(data: Any) -> Tuple[Dict[str, Any], List[str]]:
    """Validate a parsed ``solution.json`` payload.

    Returns a ``(cleaned, errors)`` pair. ``cleaned`` contains only known,
    correctly typed fields, so a partially malformed file still contributes
    whatever it got right instead of being discarded wholesale.
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return {}, ['solution metadata must be a JSON object']

    cleaned: Dict[str, Any] = {}

    for field, (expected_type, required) in SCHEMA.items():
        if field not in data or data[field] is None:
            if required:
                errors.append(f"missing required field '{field}'")
            continue

        value = data[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"field '{field}' should be a {_type_name(expected_type)}, "
                f"got {type(value).__name__}"
            )
            continue

        if expected_type is str:
            value = value.strip()
            if not value:
                if required:
                    errors.append(f"field '{field}' must not be empty")
                continue

        if expected_type is list:
            value = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if not value:
                continue

        cleaned[field] = value

    unknown = sorted(set(data) - set(SCHEMA))
    for field in unknown:
        errors.append(f"unknown field '{field}'")

    lifecycle = cleaned.get('lifecycle')
    if lifecycle is not None and lifecycle.lower() not in LIFECYCLE_STAGES:
        errors.append(
            f"lifecycle '{lifecycle}' is not one of: {', '.join(LIFECYCLE_STAGES)}"
        )
        cleaned.pop('lifecycle')
    elif lifecycle is not None:
        cleaned['lifecycle'] = lifecycle.lower()

    support = cleaned.get('support')
    if support is not None and support.lower() not in SUPPORT_LEVELS:
        errors.append(f"support '{support}' is not one of: {', '.join(SUPPORT_LEVELS)}")
        cleaned.pop('support')
    elif support is not None:
        cleaned['support'] = support.lower()

    contact = cleaned.get('contact')
    if contact is not None and '@' not in contact:
        errors.append("contact should be an email address or a GitHub @handle")

    summary = cleaned.get('summary')
    if summary is not None and len(summary) > MAX_SUMMARY_LENGTH:
        errors.append(
            f"summary is {len(summary)} characters, the maximum is {MAX_SUMMARY_LENGTH}"
        )
        cleaned['summary'] = summary[:MAX_SUMMARY_LENGTH].rstrip()

    return cleaned, errors


def parse_solution_metadata(raw: str) -> Tuple[Dict[str, Any], List[str]]:
    """Parse and validate the raw contents of a ``solution.json`` file."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, [f'invalid JSON: {exc}']
    return validate_solution_metadata(data)


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        print(f'usage: {argv[0]} path/to/solution.json', file=sys.stderr)
        return 2

    try:
        with open(argv[1], 'r', encoding='utf-8') as handle:
            raw = handle.read()
    except OSError as exc:
        print(f'could not read {argv[1]}: {exc}', file=sys.stderr)
        return 2

    cleaned, errors = parse_solution_metadata(raw)

    for error in errors:
        print(f'error: {error}', file=sys.stderr)

    print(json.dumps(cleaned, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
