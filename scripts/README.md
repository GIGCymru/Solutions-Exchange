# NHS Wales Solutions Exchange - Scripts

This directory contains automated scripts for maintaining the Solutions Exchange data.

## Scripts Overview

### 🤖 `update_repositories.py`
**Main automation script** - Fetches and enhances repository data from NHS Wales organizations.

**Features:**
- Fetches repositories from all NHS Wales GitHub organizations
- Generates AI-powered tags based on repository content
- Calculates quality scores using multiple metrics
- Identifies featured solutions automatically
- Includes comprehensive error handling and logging

**Usage:**
```bash
# Requires GITHUB_TOKEN environment variable
export GITHUB_TOKEN="your_token_here"
python scripts/update_repositories.py
```

**Automated by:** GitHub Actions (runs daily at 6 AM UTC)

### 🔍 `validate_data.py`
**Data validation script** - Validates repository data integrity and generates reports.

**Features:**
- Validates required and enhanced data fields
- Generates comprehensive statistics
- Exports summary reports
- Checks data quality and consistency

**Usage:**
```bash
python scripts/validate_data.py
```

### 🛠️ `manual_update.py`
**Development script** - Manual trigger for local development and testing.

**Features:**
- Runs the full update process locally
- Includes validation step
- User-friendly logging and error messages
- Checks for required environment variables

**Usage:**
```bash
export GITHUB_TOKEN="your_token_here"
python scripts/manual_update.py
```

### 📚 `utils.py`
**Utility functions** - Common functions used across scripts.

**Features:**
- Repository data loading/saving
- Statistics calculation
- Data validation functions
- Organization name mapping
- Report generation

## Data Flow

```
GitHub Organizations
        ↓
update_repositories.py  ← Fetches & enhances data
        ↓
data/repositories.json  ← Enhanced repository data
        ↓
validate_data.py       ← Validates data integrity
        ↓
Website Display        ← Featured solutions, quality scores, AI tags
```

## GitHub Actions Integration

The scripts are fully integrated with GitHub Actions for automated updates:

- **Schedule**: Daily at 6 AM UTC
- **Triggers**: Manual dispatch, script changes
- **Output**: Updated `data/repositories.json`
- **Validation**: Automatic data validation
- **Logging**: Comprehensive workflow summaries

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with repo access |
| `GH_SECRET` | Alternative | Alternative name for GitHub token |

## Output Files

| File | Description |
|------|-------------|
| `data/repositories.json` | Main repository data with enhancements |
| `data/summary_report.json` | Statistical summary and featured repositories |
| `update.log` | Detailed execution logs |

## Quality Scoring Algorithm

The quality scoring system evaluates repositories on multiple criteria:

- **Base Score**: 50 points (starting baseline)
- **Community Engagement**: 0-20 points (GitHub stars)
- **Recent Activity**: 0-15 points (recent commits)
- **Documentation**: 0-15 points (README, description quality)
- **Technical Implementation**: 0-10 points (language, topics)
- **Repository Activity**: 0-10 points (size, development activity)
- **Open Source Practices**: 0-5 points (license)

**Range**: 30-100 points

## Featured Solution Criteria

Solutions are automatically featured when they meet these thresholds:

- **High Quality**: Quality score ≥ 80 (automatic)
- **Community Endorsed**: Quality score ≥ 70 + community stars
- **Recent & Quality**: Quality score ≥ 65 + recent activity (< 60 days)

## AI Tag Generation

Tags are generated based on:

- Repository name and description analysis
- Programming language detection
- Healthcare domain keywords
- NHS-specific terminology
- Technical implementation patterns

## Error Handling

All scripts include comprehensive error handling:

- **Network errors**: Retry logic with exponential backoff
- **Rate limiting**: Automatic rate limit detection and waiting
- **Data validation**: Schema validation and integrity checks
- **Logging**: Detailed logging with multiple output formats

## Maintenance

### Adding New Organizations

Update the `organizations` list in `update_repositories.py`:

```python
self.organizations = [
    "existing-org",
    "new-nhs-organization",  # Add here
]
```

### Modifying Quality Criteria

Update the `calculate_quality_score()` method in `update_repositories.py` to adjust scoring weights.

### Adding New Tag Categories

Update the `generate_ai_tags()` method in `update_repositories.py` to include new healthcare or technical domains.

## Troubleshooting

### Common Issues

1. **GitHub Token Issues**
   - Ensure token has `repo` scope
   - Check token hasn't expired
   - Verify organization access permissions

2. **Rate Limiting**
   - Scripts include automatic rate limit handling
   - Consider using GitHub App tokens for higher limits

3. **Data Validation Errors**
   - Run `validate_data.py` to identify issues
   - Check `update.log` for detailed error information

### Support

For issues or questions:
1. Check the workflow logs in GitHub Actions
2. Review the `update.log` file
3. Run validation script for data integrity issues
4. Contact the NHS Wales GIG Cymru team
