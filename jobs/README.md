# Jobs System

Data collection jobs managed by `job_manager.py`. Each job scrapes/processes data and outputs structured files.

## Quick Start

```bash
# Run a job
python job_manager.py run --job chrome_extensions_scraper

# List all jobs
python job_manager.py list
```

## Adding a New Job

### 1. Create Directory Structure
```bash
mkdir jobs/my_new_job
```

### 2. Create `job_config.json`
```json
{
  "job_id": "my_new_job_scraper",
  "name": "My New Job Scraper", 
  "description": "What this job does",
  "enabled": true,
  "source": {
    "type": "script",
    "script_path": "main.py",
    "working_directory": "jobs/my_new_job",
    "timeout_seconds": 3600
  },
  "output": {
    "format": "csv",
    "directory": "output", 
    "filename": "results.csv"
  }
}
```

### 3. Create `main.py`
```python
import pandas as pd
import os

def main():
    # Your scraping/processing logic
    data = [{"example": "data"}]
    
    # Save results
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv("output/results.csv", index=False)
    print(f"✅ Processed {len(data)} records")

if __name__ == "__main__":
    main()
```

### 4. Test
```bash
python job_manager.py run --job my_new_job_scraper
```

## Current Jobs

- **chrome_extensions_scraper**: Chrome Web Store extension data
- **gitleaks_rules_scraper**: Gitleaks security rules from GitHub  
- **vscode_extensions_scraper**: VSCode Marketplace extension data

## Configuration Fields

**Required:**
- `job_id`: Unique identifier
- `name`: Human-readable name
- `enabled`: true/false
- `source.type`: "script"
- `source.script_path`: Script filename
- `source.working_directory`: Job directory path
- `output.format`: "csv" or "json"
- `output.directory`: Output folder
- `output.filename`: Output file name

**Optional:**
- `source.timeout_seconds`: Max runtime (default: 3600)
- `source.retry_attempts`: Retry count
- `source.retry_delay_seconds`: Delay between retries

## Tips

- Jobs must output CSV/JSON files in the specified directory
- Use `print()` statements for logging during execution
- Check `job_manager.log` for detailed execution logs
- Test jobs before enabling them