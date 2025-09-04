import argparse
import sys
import subprocess
import logging
import psutil
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path
import pandas as pd


# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class JobExecution:
    """Represents a single job execution."""
    execution_id: str
    job_id: str
    job_name: str
    started_at: datetime
    status: str = 'running'
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    retry_attempt: int = 0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None


@dataclass
class Job:
    job_id: str
    name: str
    config_file: str


def _generate_execution_id() -> str:
    """Generate unique execution ID."""
    import uuid
    return str(uuid.uuid4())


def _process_job_output(config: Dict) -> int:
    """Process job output and update database."""
    source_config = config['source']
    output_config = config.get('output', {})
    records_processed = 0

    try:
        # Parse output to find output file path
        output_path = source_config['working_directory'] + '/' + output_config.get('directory') + '/' + output_config.get('filename')

        # Import data using our existing import infrastructure
        output_format = output_config.get('format', 'csv')

        if output_format == 'json':
            try:
                with open(output_path, 'w') as output_file:
                    result = json.load(output_file)
                    records_processed = len(result)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"Output file {output_path} could not be proceed: {e}")

        elif output_format == 'csv':
            try:
                df = pd.read_csv(output_path)
                records_processed = len(df)
                logger.info(f"📄 Found {records_processed} rows in CSV file")
            except pd.errors.ParserError as e:
                logger.error(f"Output file {output_path} could not be processed: {e}")

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return records_processed

    except Exception as e:
        logger.error(f"❌ Failed to process job output: {e}")
        raise


def _run_script_job(config: Dict) -> int:
    """Execute a script-based job."""
    source_config = config['source']

    script_path = source_config['script_path']
    working_dir = source_config.get('working_directory', '.')
    python_env = source_config.get('python_env', 'python')
    timeout = source_config.get('timeout_seconds', 3600)

    # Prepare command
    cmd = [python_env, script_path]
    logger.debug(f'Running command: {python_env} {script_path} from dir: {working_dir}')

    # Execute script
    try:
        # ToDo: pass the config as argument
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        logger.info(f'Job Logs:\n{"="*30}\n{result.stdout}{"="*30}')

        if result.returncode != 0:
            raise Exception(f"Script failed with code {result.returncode}: {result.stderr}")

        # Process output and update database
        return _process_job_output(config)

    except subprocess.TimeoutExpired:
        raise Exception(f"Script timed out after {timeout} seconds")


class JobManager:
    """Main job management system."""
    
    def __init__(self, jobs_dir: str = "jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.connection = None
        self.cursor = None
        self.jobs_config = {}

    def load_job_configs(self) -> Dict[str, Dict]:
        """Load all job configurations from JSON files."""
        configs = {}
        
        if not self.jobs_dir.exists():
            logger.warning(f"⚠️ Jobs directory {self.jobs_dir} does not exist")
            return configs
        config_files = [file for folder in self.jobs_dir.iterdir() for file in folder.iterdir() if file.name.endswith("job_config.json")]
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                job_id = config.get('job_id')
                if not job_id:
                    logger.warning(f"⚠️ Config file {config_file} missing job_id")
                    continue

                # ToDo load config to Job data type
                config['_config_file'] = str(config_file)
                configs[job_id] = config
                
                (logger.debug(f"📄 Loaded config for job: {job_id}"))
                
            except Exception as e:
                logger.error(f"❌ Failed to load config {config_file}: {e}")
        
        self.jobs_config = configs
        logger.info(f"📋 Loaded {len(configs)} job configurations")
        return configs

    def run_job(self, job_id: str, force: bool = False) -> JobExecution | None:
        """Execute a specific job."""
        if job_id not in self.jobs_config:
            raise ValueError(f"Job '{job_id}' not found in configurations")
        
        config = self.jobs_config[job_id]
        
        if not config.get('enabled', True) and not force:
            logger.warning(f"⚠️ Job '{job_id}' is disabled. Use --force to run anyway.")
            return None
        
        # Create execution record
        execution = JobExecution(
            execution_id=_generate_execution_id(),
            job_id=job_id,
            job_name=config.get('name', job_id),
            started_at=datetime.now()
        )

        try:
            logger.info(f"🚀 Starting job: {job_id}")
            
            # Get system info before execution
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu = psutil.cpu_percent()
            
            # Execute the job
            if config['source']['type'] == 'script':
                result = _run_script_job(config)
            else:
                raise ValueError(f"Unsupported source type: {config['source']['type']}")
            
            # Calculate performance metrics
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            execution.status = 'completed'
            execution.completed_at = datetime.now()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.cpu_usage = end_cpu - start_cpu
            execution.memory_usage = end_memory - start_memory
            
            # Update with results
            if result:
                execution.records_processed = result
            
            logger.info(f" ✅ Job '{job_id}' completed successfully")
            logger.info(f"   Duration: {execution.duration_seconds}s")
            logger.info(f"   Records processed: {execution.records_processed}")
            
        except Exception as e:
            execution.status = 'failed'
            execution.completed_at = datetime.now()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.error_message = str(e)
            
            logger.error(f"❌ Job '{job_id}' failed: {e}")
            logger.error(f"   Duration: {execution.duration_seconds}s")
            
        return execution


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Content Feeds Job Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a specific job')
    run_parser.add_argument('--job', required=True, help='Job ID to run')
    run_parser.add_argument('--force', action='store_true', help='Force run even if disabled')

    # List command
    subparsers.add_parser('list', help='List all jobs')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = JobManager()
        manager.load_job_configs()
        
        if args.command == 'run':
            manager.run_job(args.job, force=args.force)

        elif args.command == 'list':
            print("-" * 80)
            for job in manager.jobs_config:
                job_config = manager.jobs_config[job]
                status = " ✅" if job_config['enabled'] else "⏸️"
                print(f"{job_config['name']}: {status}")
                print(f"\tJob ID: {job_config['job_id']}")
                print(f"\tOutput file: {job_config['source']['working_directory']}/{job_config['output']['directory']}/{job_config['output']['filename']}")
                print()
        
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
    # job_manager = JobManager()
    # job_manager.load_job_configs()
    # job_manager.run_job('gitleaks_rules_scraper')
