# marketplace_crawler.py
"""
VSCode Extensions Marketplace Crawler

This module provides functionality to crawl and download extension data
from the Visual Studio Code Marketplace.
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def extension_pricing(extension):
    try:
        for version in extension['versions']:
            if 'properties' not in version:
                continue
            for prop in version['properties']:
                if prop['key'] == 'Microsoft.VisualStudio.Services.Content.Pricing':
                    return prop['value']

    except KeyError:
        return None


@dataclass
class MarketplaceConfig:
    """Configuration for VSCode Marketplace API."""
    url: str = 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery'
    headers: Dict[str, str] = None


class MarketplaceCrawler:
    """Crawler for VSCode Marketplace extensions."""

    def __init__(self, config: MarketplaceConfig = None):
        self.config = config or MarketplaceConfig()
        self.payload = self._get_default_payload()
        self._setup_output_directory()

    @staticmethod
    def _get_default_payload() -> Dict:
        """Get default payload for the API request."""
        return {
            "filters": [{
                "criteria": [
                    {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                    {"filterType": 10, "value": "target:\"Microsoft.VisualStudio.Code\" "},
                ],
                "direction": 2,
                "pageSize": 1000,
                "pageNumber": 1,
                "sortBy": 4,
                "sortOrder": 0,
            }],
            "flags": 870
        }

    def _setup_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs('extensions', exist_ok=True)

    def _make_request(self, page: int) -> Optional[List[Dict]]:
        """Make API request for a specific page."""
        try:
            self.payload['filters'][0]['pageNumber'] = page
            response = requests.post(
                self.config.url,
                headers=self.config.headers,
                json=self.payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('results', [{}])[0].get('extensions', [])
        except RequestException as e:
            logger.error(f"Error making request for page {page}: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing response for page {page}: {str(e)}")
            return None

    def _save_extensions(self, extensions: List[Dict], page: int) -> None:
        """Save extensions data to JSON file."""
        try:
            # Remove version information to reduce file size
            for extension in extensions:
                extension_str = json.dumps(extension)
                has_icon = 'Microsoft.VisualStudio.Services.Icons.Default' in extension_str
                extension['hasIcon'] = has_icon
                extension['pricing'] = extension_pricing(extension)
                extension.pop('versions', None)

            output_path = os.path.join('extensions', f'{page}.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(extensions, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving extensions for page {page}: {str(e)}")

    def crawl(self, max_pages: int = 1000) -> int:
        """
        Crawl the VSCode Marketplace for extensions.

        Args:
            max_pages: Maximum number of pages to crawl

        Returns:
            Total number of extensions crawled
        """
        total_extensions = 0

        for page in range(1, max_pages + 1):
            extensions = self._make_request(page)

            if not extensions:
                logger.info(f"No more extensions found after page {page - 1}")
                break

            total_extensions += len(extensions)
            logger.info(f"Crawled page {page}: Found {len(extensions)} extensions "
                        f"(Total: {total_extensions})")

            self._save_extensions(extensions, page)

        return total_extensions


def main():
    """Main entry point for the crawler."""
    try:
        crawler = MarketplaceCrawler()
        total_extensions = crawler.crawl()
        logger.info(f"Crawling completed. Total extensions: {total_extensions}")
    except Exception as e:
        logger.error(f"Unexpected error during crawling: {str(e)}")
        raise


if __name__ == '__main__':
    main()