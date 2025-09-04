import json
import logging
import random
import time
import urllib.parse
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class ChromeWebStoreAPIClient:
    """Chrome Web Store API client for making requests."""
    
    BASE_URL = "https://chromewebstore.google.com/_/ChromeWebStoreConsumerFeUi/data/batchexecute"

    def __init__(self,
                 delay_range: tuple = (1, 3),
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            delay_range: Tuple of (min, max) seconds to wait between requests
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a properly configured requests session."""
        session = requests.Session()

        # Set realistic browser headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': 'https://chromewebstore.google.com',
            'Referer': 'https://chromewebstore.google.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })

        return session

    def build_request_data(self,
                          query: str = "productivity/education",
                          amount: int = 32,
                          page_token: Optional[str] = None) -> str:
        """
        Build request data for the Chrome Web Store API.
        
        Args:
            query: Search query or category
            amount: Number of results per page (default: 32)
            page_token: Token for pagination (None for first page)
            
        Returns:
            URL-encoded request data
        """
        if page_token is None:
            # First page request - use amount only
            request_data = [
                [
                    [
                        "zTyKYc",
                        f'[[null,[[3,"{query}",null,null,2,[{amount}]]]]]',
                        None,
                        "generic"
                    ]
                ]
            ]
        else:
            # Subsequent pages - use amount and page token
            request_data = [
                [
                    [
                        "zTyKYc",
                        f'[[null,[[3,"{query}",null,null,2,[{amount},"{page_token}"]]]]]',
                        None,
                        "generic"
                    ]
                ]
            ]

        # Convert to JSON and URL encode
        json_data = json.dumps(request_data)
        encoded_data = urllib.parse.quote(json_data)

        return f"f.req={encoded_data}"

    def make_request_with_retry(self, data: str) -> str:
        """
        Make HTTP request with retry logic.
        
        Args:
            data: URL-encoded request data
            
        Returns:
            Raw response text
            
        Raises:
            requests.RequestException: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making request (attempt {attempt + 1}/{self.max_retries})")

                response = self.session.post(
                    self.BASE_URL,
                    data=data,
                    timeout=self.timeout
                )
                response.raise_for_status()

                logger.debug(f"Request successful, response length: {len(response.text)}")
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise

        return ""

    def add_delay(self):
        """Add delay between requests."""
        delay = random.uniform(*self.delay_range)
        logger.debug(f"Waiting {delay:.1f} seconds before next request...")
        time.sleep(delay)

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()