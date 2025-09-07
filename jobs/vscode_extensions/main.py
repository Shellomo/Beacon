import json
import os
from pathlib import Path


with open('job_config.json', 'r') as config_file:
    job_config = json.load(config_file)
output_config = job_config['output']
output_dir = Path(output_config['directory'])
output_filename = Path(output_config['filename'])
output_file_path = output_dir / output_filename
os.makedirs(output_dir, exist_ok=True)


try:
    from marketplace_crawler import MarketplaceCrawler
    from data_processor import ExtensionDataProcessor

    print("🚀 Starting VSCode Marketplace scraper")
    
    # Initialize the crawler
    crawler = MarketplaceCrawler()

    # Start crawling (default: max_pages=1000)
    total_extensions = crawler.crawl(max_pages=1000)
    
    # Initialize the processor
    processor = ExtensionDataProcessor()
    
    # Convert to CSV
    processor.convert_to_csv(output_file=output_file_path)

    # delete extensions JSON files after processing
    for file_path in os.listdir(processor.extensions_dir):
        # delete the file
        file_path = processor.extensions_dir / file_path
        os.remove(file_path)
    os.rmdir(processor.extensions_dir)
    print("Cleaned up JSON files after processing.")

except Exception as e:
    print(f"❌ VSCode scraper failed: {e}")
    exit(1)
