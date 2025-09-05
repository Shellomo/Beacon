"""
Gitleaks Security Rules Scraper

Fetches the latest Gitleaks security detection rules from GitHub
and outputs them in JSONL format for database import.

Source: https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml
"""
import csv
import logging
import os
from pathlib import Path

import requests
import json
import sys
from typing import Dict, List, Any
import tomllib
from models import GitleakRule


with open('job_config.json', 'r') as config_file:
    job_config = json.load(config_file)
output_config = job_config['output']
output_dir = Path(output_config['directory'])
output_filename = Path(output_config['filename'])
os.makedirs(output_dir, exist_ok=True)

# GitHub raw URL for the gitleaks.toml file
GITLEAKS_RAW_URL = 'https://raw.githubusercontent.com/gitleaks/gitleaks/master/config/gitleaks.toml'


logger = logging.getLogger(__name__)


def fetch_gitleaks_config() -> str:
    """Fetch the gitleaks.toml configuration from GitHub."""
    try:
        print("🔍 Fetching Gitleaks configuration from GitHub...")
        response = requests.get(GITLEAKS_RAW_URL, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Successfully fetched {len(response.text)} characters from GitHub")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch Gitleaks config: {e}")
        raise


def extract_rules(content: str) -> List[GitleakRule] | None:
    """
    Simple TOML parser for gitleaks.toml structure.
    This assumes the specific format of the gitleaks config.
    """
    try:
        data = tomllib.loads(content)
        raw_rules = data['rules']
        rules = []
        for rule in raw_rules:
            rules.append(GitleakRule(
                rule_id=rule.get('id'),
                name=rule.get('id'),
                description=rule.get('description'),
                regex=rule.get('regex'),
            ))
        return rules

    except Exception as e:
        print(f"⚠️ tomllib parsing failed: {e}")
        return None


def transform_rules_to_jsonl(parsed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform parsed TOML rules into JSONL format for database."""
    rules = parsed_config.get('rules', [])
    transformed_rules = []
    
    for i, rule in enumerate(rules):
        
        transformed_rule = {
            'rule_id': rule.get('id'),
            'name': rule.get('id', f"Gitleaks Rule {i + 1}"),
            'description': rule.get('description', 'No description available'),
            'regex': rule.get('regex', '')
        }
        
        # Clean up None values
        transformed_rule = {k: v for k, v in transformed_rule.items() if v is not None}
        transformed_rules.append(transformed_rule)
    
    return transformed_rules


def save_to_csv(rules: List[GitleakRule], filename: Path):
    """
    Save extensions to CSV file.

    Args:
        rules: List of GitleakRule objects
        filename: Output filename
    """
    if not rules:
        logger.warning("No extensions to save")
        return

    fieldnames = list(rules[0].to_dict().keys())

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rule in rules:
            row = rule.to_dict()
            writer.writerow(row)

    logger.info(f"Saved {len(rules)} rules to {filename}")


def main():
    """Main scraper function."""
    try:
        print("🚀 Starting Gitleaks rules scraper...")
        
        # Fetch the configuration
        config_content = fetch_gitleaks_config()
        
        # Parse the TOML content
        print("📋 Parsing TOML configuration...")
        parsed_rules = extract_rules(config_content)

        if not parsed_rules:
            print("⚠️ No rules found in configuration!")
            sys.exit(1)

        output_file_path = output_dir / output_filename
        save_to_csv(parsed_rules, output_file_path)
        print(f"✅ Gitleaks scraper completed successfully!")
        print(f"📊 Total rules processed: {len(parsed_rules)}")
        print(f"📁 Output file: {output_file_path}")
        
        # Output summary for job manager to parse
        print(f"SUMMARY: {len(parsed_rules)} security rules scraped to {output_file_path}")
        
    except Exception as e:
        print(f"❌ Gitleaks scraper failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
