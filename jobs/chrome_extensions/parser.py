import json
import logging
from datetime import datetime
from typing import List, Any, Optional
from models import ChromeExtension

logger = logging.getLogger(__name__)


class ChromeStoreParser:
    """Parser for Chrome Web Store API responses."""
    
    @staticmethod
    def fix_json_response(response_text: str) -> List[List[Any]]:
        """
        Fix and parse JSON response using the proven approach.
        
        This is the working parsing logic that handles the Chrome Web Store's
        nested JSON response format.
        
        Args:
            response_text: Raw API response
            
        Returns:
            List of raw extension data arrays
            
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Extract the JSON part from the response
            if "[[[[[" not in response_text:
                raise ValueError("Response does not contain expected JSON structure")

            step1 = "[[[[[" + response_text.split("[[[[[")[1]
            step2 = step1.split("]]]]]]")[0] + "]]]]]]"
            step3 = step2.replace("\\\\", "\\")
            step4 = step3.replace('\\"', '"')
            step5 = step4.replace("\n", "")
            step6 = step5[:-2]  # Remove trailing comma
            step7 = json.loads(step6)[0][0]

            return step7

        except (IndexError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

    @staticmethod
    def extract_pagination_token(response_text: str) -> Optional[str]:
        """
        Extract pagination token from API response.
        
        Args:
            response_text: Raw API response
            
        Returns:
            Next page token or None if no more pages
        """
        try:
            token_phase1 = response_text.split('[\\"')
            # if len(token_phase1) == 66:
            token_phase2 = token_phase1[-1]
            token = token_phase2.split('\\')[0]
            return token
            
        except Exception as e:
            logger.debug(f"Failed to extract pagination token: {e}")
            import os
            os.makedirs("output", exist_ok=True)
            with open("output/debug_response.txt", "w") as f:
                f.write(response_text)
            logger.info(f"Saved debug response to output/debug_response.txt")
            return None

    @staticmethod
    def parse_extension_data(item: List[Any]) -> Optional[ChromeExtension]:
        """
        Parse individual extension data from API response array.
        
        Args:
            item: Raw extension data array from API
            
        Returns:
            ChromeExtension object or None if parsing fails
        """
        try:
            if not item:
                logger.info("No extension data found")
                return None

            # Parse manifest JSON if available
            manifest = {}
            if item[18] and isinstance(item[18], str):
                try:
                    manifest = json.loads(item[18])
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse manifest for extension {item[0]}")
                    manifest = {}
            version = manifest.get('version', 'Unknown')
            host_wide_permissions = False
            if 'permissions' in manifest and 'host_permissions' in manifest and isinstance(manifest['host_permissions'], list):
                host_wide_permissions = any(perm in ["http://*/*", "https://*/*"] for perm in manifest['host_permissions'])

            # Parse creation date from timestamp
            create_date = "Unknown"
            if item[17] and isinstance(item[17], list) and len(item[17]) > 0:
                try:
                    timestamp = float(item[17][0])
                    create_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                except (ValueError, IndexError, TypeError):
                    logger.debug(f"Failed to parse date for extension {item[0]}")

            # Parse rating
            rating = None
            if item[3] and str(item[3]).replace('.', '').replace('-', '').isdigit():
                rating = round(float(item[3]), 2)

            # Parse rating count
            rating_count = None
            if item[4] and str(item[4]).isdigit():
                rating_count = int(item[4])

            # Parse category
            category = None
            if item[11] and isinstance(item[11], list) and len(item[11]) > 0:
                category = str(item[11][0])

            # Parse users count
            downloads = None
            if item[14]:
                downloads = str(item[14]) if not str(item[14]).isdigit() else int(item[14])

            extension = ChromeExtension(
                id=str(item[0]) if item[0] else "",
                name=str(item[2]) if item[2] else "",
                display_name=str(item[19]) if len(item) > 19 and item[19] else "",
                short_description=str(item[6]) if item[6] else "",
                category=category,
                icon_link=str(item[1]) if item[1] else "",

                downloads=downloads,
                rating=rating,
                rating_count=rating_count,

                website=str(item[7]) if item[7] else None,
                good_record=bool(item[8]) if item[8] is not None else False,
                featured=bool(item[9]) if item[9] is not None else False,

                create_date=create_date,
                version=version,
                host_wide_permissions=host_wide_permissions
            )

            # Basic validation
            if not extension.id or not extension.name:
                logger.info(f"Failed to parse extension {item[0]}")
                return None
            # logger.info(f"Parsed extension: {extension.id} - {extension.name}")
            return extension

        except Exception as e:
            logger.info(f"Error parsing extension data: {e}")
            return None