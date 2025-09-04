import json
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import config
from models import ChromeExtension
from api_client import ChromeWebStoreAPIClient
from parser import ChromeStoreParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

with open('job_config.json', 'r') as config_file:
    job_config = json.load(config_file)
source_config = job_config['source']
output_config = job_config['output']
working_dir = Path(source_config['working_directory'])
output_dir = Path(output_config['directory'])
output_filename = Path(output_config['filename'])
output_file_path = working_dir/ output_dir / output_filename
os.makedirs(output_dir, exist_ok=True)


def save_to_csv(extensions: List[ChromeExtension], filename: Path):
    """
    Save extensions to CSV file.

    Args:
        extensions: List of ChromeExtension objects
        filename: Output filename
    """
    if not extensions:
        logger.warning("No extensions to save")
        return

    fieldnames = list(extensions[0].to_dict().keys())

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ext in extensions:
            row = ext.to_dict()
            # Convert complex fields to strings
            # row['manifest'] = json.dumps(row['manifest']) if row['manifest'] else ""
            writer.writerow(row)

    logger.info(f"Saved {len(extensions)} extensions to {filename}")


def get_extension_summary(extensions: List[ChromeExtension]) -> Dict[str, Any]:
    """
    Get summary statistics for a list of extensions.

    Args:
        extensions: List of ChromeExtension objects

    Returns:
        Dictionary with summary statistics
    """
    if not extensions:
        return {"total": 0}

    # Calculate statistics
    total = len(extensions)
    rated_extensions = [ext for ext in extensions if ext.rating is not None]
    avg_rating = sum(ext.rating for ext in rated_extensions) / len(rated_extensions) if rated_extensions else 0

    categories = {}
    for ext in extensions:
        if ext.category:
            categories[ext.category] = categories.get(ext.category, 0) + 1

    return {
        "total": total,
        "with_ratings": len(rated_extensions),
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "categories": categories,
        "featured": len([ext for ext in extensions if ext.featured])
    }


class ChromeWebStoreScraper:
    """
    Chrome Web Store scraper using the official API endpoints.
    
    Features:
    - Category-based searching
    - Query-based searching  
    - Rate limiting and retry logic
    - Error handling
    - Data export capabilities
    """

    def __init__(self,
                 delay_range: tuple = (1, 3),
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Initialize the scraper.
        
        Args:
            delay_range: Tuple of (min, max) seconds to wait between requests
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self.api_client = ChromeWebStoreAPIClient(delay_range, max_retries, timeout)
        self.parser = ChromeStoreParser()

    def search_by_category(self,
                           category: str = "productivity/education",
                           results_per_page: Optional[int] = None,
                           max_pages: int = 10) -> List[ChromeExtension]:
        """
        Search extensions by category with pagination support.
        
        Args:
            category: Category to search (e.g., "productivity/education", "lifestyle", "developer_tools")
            results_per_page: Maximum number of results to return (None for all available)
            max_pages: Maximum number of pages to fetch (default: 10)
            
        Returns:
            List of ChromeExtension objects
        """
        logger.info(f"Searching category: {category} (items per page: {results_per_page}, max pages: {max_pages})")
        
        all_extensions = []
        page_token = None
        page_count = 0
        
        while page_count < max_pages:
            page_count += 1
            logger.info(f"Fetching page {page_count}...")
            
            # Build and make request
            data = self.api_client.build_request_data(query=category, amount=results_per_page, page_token=page_token)
            response_text = self.api_client.make_request_with_retry(data)
            
            # Parse response
            try:
                raw_extensions = self.parser.fix_json_response(response_text)
                logger.info(f"Found {len(raw_extensions)} raw extension entries on page {page_count}")
                
                if not raw_extensions:
                    logger.info("No more extensions found - stopping pagination")
                    break
                
                # Convert to ChromeExtension objects
                page_extensions = []
                for item in raw_extensions:
                    if len(item) > 0:  # Each item is [extension_data]
                        extension = self.parser.parse_extension_data(item[0])
                        if extension:
                            page_extensions.append(extension)
                
                all_extensions.extend(page_extensions)
                logger.info(f"Page {page_count}: Added {len(page_extensions)} extensions (total: {len(all_extensions)})")
                
                # Extract pagination token for next page
                next_token = self.parser.extract_pagination_token(response_text)
                if not next_token:
                    logger.info("No pagination token found - reached last page")
                    break
                
                page_token = next_token
                
                # Add delay between pages
                if page_count < max_pages:
                    self.api_client.add_delay()
                
            except Exception as e:
                logger.error(f"Failed to process page {page_count}: {e}")
                break
        
        logger.info(f"Successfully scraped {len(all_extensions)} extensions across {page_count} pages")
        return all_extensions

    def save_to_json(self, extensions: List[ChromeExtension], filename: str, indent: int = 2):
        """
        Save extensions to JSON file.
        
        Args:
            extensions: List of ChromeExtension objects
            filename: Output filename
            indent: JSON indentation (default: 2)
        """
        data = [ext.to_dict() for ext in extensions]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)

        logger.info(f"Saved {len(extensions)} extensions to {filename}")

    def close(self):
        """Close the session and cleanup resources."""
        self.api_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    with open('store_categories.json', 'r') as f:
        categories = json.load(f)

    with ChromeWebStoreScraper(delay_range=(0.5, 1.5)) as scraper:
        logger.info("Chrome Web Store Scraper Started...")

        all_extensions = []
        for category in categories:

            extensions = scraper.search_by_category(
                category,
                results_per_page=config.RESULTS_PER_PAGE,
                max_pages=config.MAX_QUERIES_PER_CATEGORY
            )
            all_extensions.extend(extensions)

        if all_extensions:
            logger.info(f"Found {len(all_extensions)} extensions")
            save_to_csv(all_extensions, filename=output_file_path)
            logger.info("Saved to jsonl")

        else:
            print("No extensions found")


if __name__ == "__main__":
    main()
