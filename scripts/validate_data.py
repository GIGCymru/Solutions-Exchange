#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Data Validation
Script to validate repository data integrity and generate reports
"""

import sys
import logging
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from utils import load_repositories, validate_repository_data, export_summary_report, get_repository_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main validation routine."""
    logger.info("Starting NHS Wales Solutions Exchange data validation")
    
    # Load repository data
    repositories = load_repositories()
    if not repositories:
        logger.error("No repository data found or failed to load")
        sys.exit(1)
    
    logger.info(f"Loaded {len(repositories)} repositories")
    
    # Validate data
    validation = validate_repository_data(repositories)
    
    # Report validation results
    if validation['valid']:
        logger.info("✅ Data validation passed!")
    else:
        logger.error("❌ Data validation failed!")
        for error in validation['errors']:
            logger.error(f"  ERROR: {error}")
    
    # Report warnings
    if validation['warnings']:
        logger.warning(f"Found {len(validation['warnings'])} warnings:")
        for warning in validation['warnings'][:5]:  # Show first 5 warnings
            logger.warning(f"  WARNING: {warning}")
        if len(validation['warnings']) > 5:
            logger.warning(f"  ... and {len(validation['warnings']) - 5} more warnings")
    
    # Display statistics
    stats = validation['statistics']
    logger.info("📊 Repository Statistics:")
    logger.info(f"  Total Repositories: {stats['total_repositories']}")
    logger.info(f"  Featured Repositories: {stats['featured_repositories']} ({stats['featured_percentage']}%)")
    logger.info(f"  Average Quality Score: {stats['average_quality_score']}")
    logger.info(f"  Recently Active: {stats['recently_active']}")
    
    # Top languages
    if stats['languages']:
        top_languages = list(stats['languages'].items())[:5]
        logger.info(f"  Top Languages: {', '.join([f'{lang}({count})' for lang, count in top_languages])}")
    
    # Top organizations
    if stats['organizations']:
        top_orgs = list(stats['organizations'].items())[:3]
        logger.info(f"  Top Organizations: {', '.join([f'{org}({count})' for org, count in top_orgs])}")
    
    # Export summary report
    if export_summary_report(repositories):
        logger.info("📄 Summary report exported successfully")
    
    # Exit with appropriate code
    sys.exit(0 if validation['valid'] else 1)

if __name__ == "__main__":
    main()
