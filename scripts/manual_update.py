#!/usr/bin/env python3
"""
NHS Wales Solutions Exchange - Manual Update Script
For local development and testing
"""

import os
import sys
import logging
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from update_repositories import NHSWalesRepositoryFetcher
from validate_data import main as validate_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Manual update script for development."""
    logger.info("NHS Wales Solutions Exchange - Manual Update")
    logger.info("=" * 50)
    
    # Check for GitHub token
    token = os.getenv('GH_SECRET') or os.getenv('GITHUB_TOKEN')
    if not token:
        logger.error("❌ GitHub token not found!")
        logger.error("Set GH_SECRET or GITHUB_TOKEN environment variable")
        logger.error("Example: export GITHUB_TOKEN='your_token_here'")
        sys.exit(1)
    
    logger.info("✅ GitHub token found")
    
    # Run the update
    logger.info("🔄 Starting repository data update...")
    fetcher = NHSWalesRepositoryFetcher()
    
    try:
        success = fetcher.run()
        if success:
            logger.info("✅ Update completed successfully!")
            
            # Run validation
            logger.info("🔍 Running data validation...")
            validate_main()
            
        else:
            logger.error("❌ Update failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⚠️ Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
