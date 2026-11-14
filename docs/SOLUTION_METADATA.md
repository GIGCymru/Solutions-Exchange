# Solution metadata standard

Most of what the Solutions Exchange knows about a repository comes from the
GitHub API: name, description, topics, licence, language and activity. That is
enough to list a repository, but not enough to answer the questions a team
actually has when they are deciding whether to reuse something:

- Who do I talk to?
- Is this a live service or somebody's weekend prototype?
- Has it been through clinical safety or information governance review?
- What does it depend on?

The current data bears this out. `scripts/data_quality_report.py` shows that
only a small fraction of indexed repositories carry enough description and
topics to be discoverable, and none of them carry reuse information at all.

`solution.json` is how a team answers those questions once, in their own
repository, so the Solutions Exchange can publish it.

## Where the file goes

Commit the file to your repository at either of these paths:

1. `solution.json` (preferred)
2. `.github/solution.json`

The daily pipeline checks them in that order and uses the first one it finds.

## Why JSON and not YAML

The format is JSON so that it can be read and validated with the Python
standard library. The data job and CI therefore need no extra dependency, and
a malformed file is caught with an exact line and column rather than a silent
misparse.

## Example

```json
{
  "contact": "digital.team@wales.nhs.uk",
  "organisation": "Digital Health and Care Wales",
  "lifecycle": "live",
  "support": "supported",
  "summary": "Forecasts emergency department attendance 7 days ahead to support staffing decisions.",
  "problem": "Rota planning relied on manual trend spotting, which under-staffed predictable surges.",
  "benefits": [
    "Reduces time spent building weekly rotas",
    "Gives a consistent forecast across health boards"
  ],
  "clinical_safety": "DCB0129 assessment completed, hazard log in docs/clinical-safety.md",
  "information_governance": "No patient identifiable data; aggregate attendance counts only",
  "dependencies": [
    "Python 3.11",
    "Access to the DHCW data platform"
  ],
  "reuse_contacts": ["@jane-doe"],
  "documentation_url": "https://example.nhs.wales/ed-forecast/docs",
  "demo_url": "https://example.nhs.wales/ed-forecast/demo"
}
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contact` | string | Yes | Email address or GitHub `@handle` for reuse enquiries. |
| `organisation` | string | No | Owning health board or organisation, if it differs from the GitHub organisation. |
| `lifecycle` | string | No | One of `idea`, `prototype`, `beta`, `live`, `maintained`, `retired`. |
| `support` | string | No | One of `none`, `best-effort`, `supported`. |
| `summary` | string | No | One or two sentences, maximum 300 characters. Longer summaries are truncated. |
| `problem` | string | No | The problem the solution addresses. |
| `benefits` | list of strings | No | Concrete benefits realised. |
| `clinical_safety` | string | No | Clinical safety position, for example a DCB0129 reference. |
| `information_governance` | string | No | Information governance position, including data classification. |
| `dependencies` | list of strings | No | Platforms, services or versions required to run it. |
| `reuse_contacts` | list of strings | No | Additional people happy to talk about reuse. |
| `documentation_url` | string | No | Link to fuller documentation. |
| `demo_url` | string | No | Link to a demo or screenshots. |

`lifecycle` and `support` are case-insensitive and are normalised to lower case
when published.

## Validation

Check a file before committing it:

```bash
python3 scripts/solution_metadata.py solution.json
```

The command prints the metadata exactly as the Solutions Exchange would publish
it, reports any problems on standard error, and exits non-zero if there were
any.

## How invalid files are treated

Validation is deliberately forgiving, because a mistake in one team's file must
never break the daily run for everyone else:

- A missing file is normal and is not an error.
- Unknown fields are reported and dropped, so the standard can grow without
  breaking older files.
- A field with the wrong type is reported and dropped, but the rest of the file
  is still published.
- An unparseable file is reported and ignored in full.

Problems are written to the pipeline log against the repository name, so they
can be found and fed back to the owning team.
