# NHS Wales Solutions Exchange Configuration

## Quick Start Guide

### 1. Set up GitHub Token
Create a GitHub Personal Access Token with `repo` permissions and set it as a secret:
- Repository Settings → Secrets and variables → Actions
- Create new secret: `GITHUB_TOKEN` (or use existing)

### 2. Enable GitHub Pages
- Repository Settings → Pages
- Source: Deploy from a branch
- Branch: `gh-pages` (will be created automatically)

### 3. Manual Data Update (Optional)
To run the data collection script manually:
```bash
export GH_SECRET=your_token_here
python fetch_repositories.py
```

### 4. Customization

#### Add/Remove Organizations
Edit `fetch_repositories.py` and modify the `organizations` list.

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
├── index.html              # Main website
├── css/style.css           # Styling
├── fetch_repositories.py   # Data collection script
├── repositories.json       # Generated data file
├── requirements.txt        # Python dependencies
├── .github/workflows/      # GitHub Actions
│   └── update-data.yml
└── README.md              # Documentation
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
