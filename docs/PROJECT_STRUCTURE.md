# Project Structure

This document outlines the organized folder structure of the NHS Wales Solutions Exchange.

## 📁 Root Directory
```
Solutions-Exchange/
├── index.html              # Main website (entry point)
├── css/                     # Stylesheets
│   └── style.css           # Main CSS file
├── data/                    # Data files
│   ├── repositories.json   # Current repository data (auto-generated)
│   └── repositories.csv    # CSV export for analysis
├── scripts/                 # Python scripts and utilities
│   ├── update_repositories.py # Main data collection script
│   ├── data_quality_report.py # Metadata completeness reporting
│   ├── utils.py               # Shared helpers and validation
│   └── main-legacy.py         # Legacy script (for reference)
├── docs/                    # Documentation and requirements
│   ├── GitHub GIG Cymru - Solutions Exchange - Project Initiation Document - v0.1.docx
│   ├── Solutions_Exchange_Functional_Requirements.xlsx
│   ├── Wireframes 1706.png
│   └── SETUP.md            # Setup and deployment guide
├── .github/                 # GitHub Actions workflows
│   └── workflows/
│       └── update-data.yml  # Automated data update workflow
├── README.md               # Main project documentation
├── requirements.txt        # Python dependencies
├── _config.yml            # GitHub Pages configuration
└── .gitignore             # Git ignore rules
```

## 📝 File Descriptions

### Core Website Files
- **index.html**: Main Solutions Exchange website with interactive features
- **css/style.css**: Professional NHS Wales themed styling

### Data Files (`data/`)
- **repositories.json**: Current repository data (auto-updated daily)
- **repositories.csv**: CSV export for data analysis

### Scripts (`scripts/`)
- **update_repositories.py**: Main script for fetching GitHub repository data, with retry, rate-limit handling and data-loss guards
- **data_quality_report.py**: Reports how complete the published solution metadata is
- **utils.py**: Shared helpers, organisation name mapping and record validation
- **main-legacy.py**: Original script (kept for reference)

### Documentation (`docs/`)
- **SOLUTION_METADATA.md**: The `solution.json` standard teams use to describe a solution
- **Project Initiation Document**: Official project requirements and scope
- **Functional Requirements**: Detailed feature specifications
- **Wireframes**: Visual design mockups
- **SETUP.md**: Quick deployment and setup guide

### Configuration Files
- **requirements.txt**: Python package dependencies
- **_config.yml**: GitHub Pages deployment configuration
- **.gitignore**: Git ignore patterns
- **.github/workflows/**: Automated CI/CD pipelines

## 🔄 Data Flow

1. **GitHub Actions** runs `scripts/update_repositories.py` daily at 6 AM UTC
2. Script fetches data from NHS Wales GitHub organizations
3. Data is saved to `data/repositories.json`
4. Website (`solutions.html`) loads data from `data/repositories.json`
5. Users interact with the Solutions Exchange interface

## 🚀 Deployment

The organized structure supports:
- **GitHub Pages** hosting (automated)
- **Clean separation** of concerns
- **Easy maintenance** and updates
- **Clear documentation** trail

All paths have been updated to reference the new organized structure.
