# data_processor.py
"""
VSCode Extensions Data Processor

This module processes crawled extension data and converts it to CSV format,
with optional export to SQLite database.
"""

import json
import csv
import logging
import os
from typing import Dict, List, Any
import pandas as pd
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExtensionFields:
    """Mapping of extension fields for data extraction."""
    FIELD_MAPPING: Dict[str, str] = None

    def __post_init__(self):
        if self.FIELD_MAPPING is None:
            self.FIELD_MAPPING = {
                'publisherId': 'publisher_publisherId',
                'publisherName': 'publisher_publisherName',
                'publisherDisplayName': 'publisher_displayName',
                'extensionId': 'extensionId',
                'extensionName': 'extensionName',
                'extensionDisplayName': 'displayName',
                'lastUpdated': 'lastUpdated',
                'publishedDate': 'publishedDate',
                'install': 'statistics_install',
                'averagerating': 'statistics_averagerating',
                'ratingcount': 'statistics_ratingcount',
                'trendingdaily': 'statistics_trendingdaily',
                'trendingmonthly': 'statistics_trendingmonthly',
                'downloadCount': 'statistics_downloadCount',
                'categories': 'categories',
                'tags': 'tags',
                'pricing': 'pricing',
                'hasIcon': 'hasIcon'
            }


class ExtensionDataProcessor:
    """Process and convert VSCode extension data to different formats."""

    def __init__(self, extensions_dir: str = 'extensions'):
        self.extensions_dir = Path(extensions_dir)
        self.fields = ExtensionFields()

    def load_extensions(self) -> List[Dict[str, Any]]:
        """Load all extension data from JSON files."""
        extensions = []
        try:
            for file_path in self.extensions_dir.glob('*.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    extensions.extend(json.load(f))
            logger.info(f"Loaded {len(extensions)} extensions from JSON files")
            return extensions
        except Exception as e:
            logger.error(f"Error loading extensions: {str(e)}")
            raise

    def _extract_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Extract value from nested dictionary using dot notation path."""
        keys = path.split('_')
        value = data
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value

    def _extract_statistic_value(self, extension: Dict[str, Any], stat_name: str) -> Any:
        """Extract value from statistics array by statistic name."""
        statistics = extension.get('statistics', [])
        for stat in statistics:
            if stat.get('statisticName') == stat_name:
                return stat.get('value')
        return None

    def _process_extension(self, extension: Dict[str, Any]) -> List[Any]:
        """Process a single extension and extract relevant values."""
        values = []

        for field_path in self.fields.FIELD_MAPPING.values():
            if field_path.startswith('statistics_'):
                stat_name = field_path.split('_')[1]
                value = self._extract_statistic_value(extension, stat_name)
            else:
                value = self._extract_nested_value(extension, field_path)

                # Format dates
                if field_path in ['lastUpdated', 'publishedDate'] and value:
                    value = value.split('T')[0]

            values.append(value)

        return values

    def convert_to_csv(self, output_file: Path = 'vscode_extensions.csv') -> None:
        """Convert extensions data to CSV format."""
        try:
            extensions = self.load_extensions()
            processed_data = [self._process_extension(ext) for ext in extensions]

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.fields.FIELD_MAPPING.keys())
                writer.writerows(processed_data)

            logger.info(f"Successfully wrote {len(processed_data)} records to {output_file}")

        except Exception as e:
            logger.error(f"Error converting to CSV: {str(e)}")
            raise

    def export_to_sqlite(self, csv_file: str = 'vscode_extensions.csv',
                         db_file: str = 'vscode_extensions.db',
                         table_name: str = 'vscode_extensions') -> None:
        """Export CSV data to SQLite database."""
        try:
            df = pd.read_csv(csv_file, low_memory=False)

            with sqlite3.connect(db_file) as conn:
                df.to_sql(table_name, conn, if_exists='replace', index=False)

            logger.info(f"Successfully exported data to SQLite database: {db_file}")

        except Exception as e:
            logger.error(f"Error exporting to SQLite: {str(e)}")
            raise


def main():
    """Main entry point for the data processor."""
    try:
        processor = ExtensionDataProcessor()
        processor.convert_to_csv()
        # processor.export_to_sqlite()

        # delete JSON files after processing
        for file_path in os.listdir(processor.extensions_dir):
            logger.info(file_path)
            file_path = processor.extensions_dir / file_path
            os.remove(file_path)
            logger.info(f"Deleted {file_path}")
        logger.info("Cleaned up JSON files after processing.")
    except Exception as e:
        logger.error(f"Unexpected error during data processing: {str(e)}")
        raise


if __name__ == '__main__':
    main()