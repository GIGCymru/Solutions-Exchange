# NHS Wales Solutions Exchange

[![Update Solutions Exchange Data](https://github.com/danThorneNDR/Solutions-Exchange/actions/workflows/update-data.yml/badge.svg)](https://github.com/danThorneNDR/Solutions-Exchange/actions/workflows/update-data.yml)

Welcome to the NHS Wales Solutions Exchange - a comprehensive platform showcasing innovative healthcare solutions, digital tools, and collaborative projects developed across NHS Wales organizations.

## 🌟 Features

- **Interactive Solution Discovery**: Browse and filter healthcare solutions by organization, topic, and project status
- **Real-time Data**: Automatically updated daily via GitHub Actions
- **Responsive Design**: Modern, mobile-friendly interface optimized for all devices
- **Advanced Filtering**: Filter by project status (Public/Internal), topics, and organizations
- **Solution Details**: Comprehensive information including descriptions, technologies, and metadata

## 🚀 Live Website

Visit the live Solutions Exchange: [https://danthornendr.github.io/Solutions-Exchange/](https://danthornendr.github.io/Solutions-Exchange/)

## 🏗️ Architecture

### Frontend
- **HTML5/CSS3/JavaScript**: Modern web standards with Bootstrap 5 framework
- **Responsive Design**: Mobile-first approach with NHS Wales branding
- **Interactive Filtering**: Real-time filtering and search capabilities

### Data Pipeline
- **Python Script**: `scripts/fetch_repositories.py` fetches data from GitHub API
- **GitHub Actions**: Automated daily updates at 6 AM UTC
- **JSON Storage**: Processed data stored in `data/repositories.json`

### Organizations Monitored
The platform tracks repositories from these NHS Wales organizations:
- Analytics Learning Programme
- Aneurin Bevan University Health Board
- Cardiff and Vale University Health Board
- Cwm Taf Morgannwg University Health Board
- Digital Health and Care Wales (DHCW)
- GitHub GIG Cymru
- Hywel Dda University Health Board
- National Data Resource (NDR)
- NHS Executive
- Powys Teaching Health Board
- Swansea Bay University Health Board

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- GitHub Personal Access Token with repo permissions

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/danThorneNDR/Solutions-Exchange.git
   cd Solutions-Exchange
   ```

2. **Install Python dependencies**:
   ```bash
   pip install requests pandas
   ```

3. **Set up environment variables**:
   ```bash
   export GH_SECRET=your_github_token_here
   ```

4. **Fetch repository data**:
   ```bash
   python scripts/fetch_repositories.py
   ```

5. **Serve the website locally**:
   ```bash
   # Using Python's built-in server
   python -m http.server 8000
   
   # Or using Node.js
   npx serve .
   ```

6. **Open in browser**: Navigate to `http://localhost:8000`

## 🔄 Data Updates

The repository data is automatically updated daily through GitHub Actions:

- **Schedule**: 6 AM UTC daily
- **Trigger**: Also runs on manual dispatch or code changes
- **Process**: Fetches latest repository information and commits changes
- **Deployment**: Automatically deploys to GitHub Pages

### Manual Update
To manually trigger a data update:
1. Go to the Actions tab in GitHub
2. Select "Update Solutions Exchange Data"
3. Click "Run workflow"

## 📊 Data Structure

Each solution includes:
- **Basic Info**: Name, description, organization
- **Technical Details**: Programming language, topics/tags
- **Metrics**: Stars, forks, last updated
- **Visibility**: Public or internal status
- **Links**: Direct links to GitHub repository and organization

## 🎨 Customization

### Styling
- Main styles: `css/style.css`
- CSS Variables for easy theming
- Bootstrap 5 for responsive layout

### Organizations
To add/remove organizations, edit the `organizations` list in `scripts/fetch_repositories.py`

### Topics/Filtering
Topics are automatically extracted from GitHub repository topics. To enhance filtering:
1. Ensure repositories have relevant topics assigned
2. Use consistent topic naming across organizations

## 🚀 Deployment

### GitHub Pages (Recommended)
The site is automatically deployed to GitHub Pages via GitHub Actions.

### Manual Deployment
1. Build the data: `python scripts/fetch_repositories.py`
2. Deploy the following files to your web server:
   - `index.html`
   - `css/style.css`
   - `data/repositories.json`

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow responsive design principles
- Maintain accessibility standards
- Test across multiple devices and browsers
- Update documentation for new features

## 📋 Requirements

Based on the Solutions Exchange Project Initiation Document:

- ✅ **Discovery Platform**: Browse solutions across NHS Wales
- ✅ **Filtering System**: Filter by organization, topic, and status
- ✅ **Responsive Design**: Works on all devices
- ✅ **Automated Updates**: Daily data refresh
- ✅ **Modern Interface**: Clean, professional design
- ✅ **Open Source**: Transparent, collaborative development

## 🔧 Troubleshooting

### Common Issues

1. **No data showing**: Check that `data/repositories.json` exists and is valid JSON
2. **GitHub API rate limits**: Ensure GitHub token is set correctly
3. **Build failures**: Check GitHub Actions logs for error details

### Support
- Create an issue in this repository
- Contact the development team through GitHub

## 📄 License

This project is part of NHS Wales digital initiatives. Please ensure compliance with NHS Wales policies and data protection requirements.

## 🙏 Acknowledgments

- NHS Wales organizations for their innovative solutions
- GitHub GIG Cymru for platform support
- Contributors and maintainers