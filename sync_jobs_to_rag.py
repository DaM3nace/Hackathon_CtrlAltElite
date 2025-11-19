"""
Sync Jobs Data to RAG System
Fetches jobs from Databricks and creates text files in documents directory
"""
import logging
import os
from pathlib import Path
from databricks_jobs import DatabricksJobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_job_for_rag(job):
    """Format a job record as a document for RAG"""
    job_text = f"""
Job Information:
- Job ID: {job.get('jobid', 'N/A')}
- Tech ID: {job.get('techid', 'N/A')}
- Job Type: {job.get('jobtype', 'N/A')}
- Order Type: {job.get('ordertype', 'N/A')}
- Customer: {job.get('customername', 'N/A')}
- Phone: {job.get('phonenumber', 'N/A')}
- Address: {job.get('customeraddress', 'N/A')}
- City: {job.get('city', 'N/A')}
- State: {job.get('state', 'N/A')}
- Appointment: {job.get('appointment', 'N/A')}
- Start Time: {job.get('starttime', 'N/A')}
- End Time: {job.get('endtime', 'N/A')}
- Duration: {job.get('durationhours', 'N/A')} hours

This is a {job.get('jobtype', 'unknown')} job of order type {job.get('ordertype', 'unknown')}
scheduled for {job.get('appointment', 'unknown date')} in {job.get('city', 'unknown city')}, {job.get('state', 'unknown state')}.
"""
    return job_text.strip()

def sync_jobs_to_rag():
    """Sync all jobs from Databricks to RAG system by creating text files"""
    try:
        # Initialize Databricks Jobs module
        logger.info("Initializing Databricks Jobs module...")
        jobs_db = DatabricksJobs()

        # Get documents directory
        docs_dir = Path(os.getenv('DOCUMENTS_DIRECTORY', 'documents'))
        docs_dir.mkdir(exist_ok=True)

        # Create jobs subdirectory
        jobs_dir = docs_dir / "jobs_data"
        jobs_dir.mkdir(exist_ok=True)

        logger.info(f"Jobs will be synced to: {jobs_dir}")

        # Get all jobs (using search with no filters)
        logger.info("Fetching jobs from Databricks...")
        jobs = jobs_db.search_jobs()

        if not jobs:
            logger.warning("No jobs found in database")
            return

        logger.info(f"Found {len(jobs)} jobs to sync")

        # Create text file for each job
        added_count = 0
        for job in jobs:
            job_id = job.get('jobid', 'unknown')
            job_text = format_job_for_rag(job)

            # Use job ID as filename
            file_path = jobs_dir / f"job_{job_id}.txt"

            # Write to file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(job_text)
                added_count += 1
                if added_count % 10 == 0:
                    logger.info(f"  Created {added_count}/{len(jobs)} job files...")
            except Exception as e:
                logger.error(f"Error creating file for job {job_id}: {str(e)}")
                continue

        logger.info(f"✅ Successfully created {added_count} job files")
        logger.info(f"\nNext step: Run databricks_embeddings.py to vectorize the job data")

    except Exception as e:
        logger.error(f"Error syncing jobs to RAG: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 80)
    print("SYNC JOBS TO RAG SYSTEM")
    print("=" * 80)
    print()

    sync_jobs_to_rag()

    print()
    print("=" * 80)
    print("SYNC COMPLETE")
    print("=" * 80)
