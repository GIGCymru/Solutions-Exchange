# NHS Wales Solutions Exchange Configuration

## Quick Start Guide

### 1. Set up GitHub Token
Create a GitHub Personal Access Token with `repo` permissions and set it as a secret:
- Repository Settings → Secrets and variables → Actions
- Create new secret: `solutions_exchange_secret`

This is the secret name `.github/workflows/update-data.yml` passes to the data
collection script.

### 2. Enable GitHub Pages
- Repository Settings → Pages
- Source: Deploy from a branch
- Branch: `gh-pages` (will be created automatically)

### 3. Manual Data Update (Optional)
To run the data collection script manually:
```bash
export solutions_exchange_secret=your_token_here
python scripts/update_repositories.py
```

### 4. Customization

#### Add/Remove Organizations
Edit `scripts/update_repositories.py` and modify the `self.organizations` list in `RepositoryUpdater.__init__`.

#### Styling Changes
Edit `css/style.css` to customize the appearance.

#### Content Updates
- Page title and descriptions: `index.html`
- Navigation links: Update navbar in `index.html`

### 5. Workflow Schedule
The data updates automatically daily at 6 AM UTC. To change:
- Edit `.github/workflows/update-data.yml`
- Modify the cron schedule

## File Structure
```
Solutions-Exchange/
├── index.html                   # Landing page
├── solutions.html               # Solution discovery and filtering
├── guides.html                  # How-to guides
├── service-metrics.html         # Platform metrics
├── css/style.css                # Styling
├── js/security.js               # Output-escaping helpers used by every page
├── scripts/
│   ├── update_repositories.py   # Data collection script run by CI
│   └── data_quality_report.py   # Metadata completeness reporting
├── data/repositories.json       # Generated data file
├── tests/                       # Python and JavaScript test suites
├── requirements.txt             # Python dependencies
├── .github/workflows/
│   ├── update-data.yml          # Daily data refresh and Pages deploy
│   └── ci.yml                   # Tests and data validation
└── README.md                    # Documentation
```

## Troubleshooting

### Data Not Loading
1. Check `repositories.json` exists and has valid JSON
2. Check browser console for errors
3. Verify GitHub Actions completed successfully

### Styling Issues
1. Clear browser cache
2. Check `css/style.css` is loading
3. Verify Bootstrap CDN links are accessible

### GitHub Actions Failing
1. Check GitHub token permissions
2. Review workflow logs in Actions tab
3. Ensure organizations are accessible with the token
