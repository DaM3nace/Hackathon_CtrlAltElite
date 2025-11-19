"""
Databricks Jobs and Techs Module
Handles querying jobs and technician information from Databricks tables
"""
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import requests

# Force .env file to override system environment variables
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabricksJobs:
    """Query jobs and technician data from Databricks"""

    def __init__(self):
        self.server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'hackathon')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'hackathon_ctrl_alt_elite')

        # Table names
        self.jobs_table = f"{self.catalog}.{self.schema}.jobs"
        self.techs_table = f"{self.catalog}.{self.schema}.techs"
        self.equipment_table = f"{self.catalog}.{self.schema}.equipmentneeded"

        self.api_url = f"https://{self.server_hostname}/api/2.0/sql/statements"

        logger.info(f"Initialized Databricks Jobs module")
        logger.info(f"  Jobs table: {self.jobs_table}")
        logger.info(f"  Techs table: {self.techs_table}")

    def execute_sql(self, sql_query: str, wait_timeout: str = "30s") -> Dict[str, Any]:
        """Execute SQL query via Databricks SQL API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "statement": sql_query,
                "warehouse_id": self.http_path.split('/')[-1],
                "wait_timeout": wait_timeout
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_tech_info(self, tech_id: str) -> Optional[Dict[str, Any]]:
        """Get technician information by tech ID"""
        try:
            sql = f"""
            SELECT *
            FROM {self.techs_table}
            WHERE UPPER(techid) = UPPER('{tech_id}')
            """

            result = self.execute_sql(sql)

            # Debug: Log the full response structure
            logger.info(f"Full API response for tech {tech_id}: {result}")

            if result.get('status') == 'error':
                logger.error(f"Failed to get tech info: {result.get('message')}")
                return None

            # Check if we have a valid result
            if 'result' not in result:
                logger.warning(f"No result key in response for tech {tech_id}")
                logger.warning(f"Available keys: {list(result.keys())}")
                return None

            result_data = result['result']
            logger.info(f"Result data keys: {list(result_data.keys())}")

            # Check if query returned data
            if 'data_array' not in result_data or not result_data['data_array']:
                logger.info(f"No data found for tech ID: {tech_id}")
                return None

            # Check if we have the manifest with schema (manifest is at top level, not in result_data)
            if 'manifest' not in result or 'schema' not in result['manifest']:
                logger.error(f"Invalid result structure - missing manifest/schema")
                logger.error(f"Full result structure: {result}")
                return None

            data_array = result_data['data_array']
            columns = [col['name'] for col in result['manifest']['schema']['columns']]
            tech_data = dict(zip(columns, data_array[0]))

            logger.info(f"Found tech info for {tech_id}: {tech_data.get('tech_name', 'Unknown')}")
            return tech_data

        except KeyError as e:
            logger.error(f"KeyError getting tech info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting tech info: {str(e)}")
            return None

    def get_jobs_for_tech(self, tech_id: str) -> List[Dict[str, Any]]:
        """Get all available jobs for a specific tech"""
        try:
            sql = f"""
            SELECT *
            FROM {self.jobs_table}
            WHERE UPPER(techid) = UPPER('{tech_id}')
            ORDER BY starttime ASC
            """

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to get jobs: {result.get('message')}")
                return []

            jobs = []
            if 'result' in result and 'data_array' in result['result']:
                columns = [col['name'] for col in result['manifest']['schema']['columns']]

                for row in result['result']['data_array']:
                    job_data = dict(zip(columns, row))
                    jobs.append(job_data)

            logger.info(f"Found {len(jobs)} jobs for tech {tech_id}")
            return jobs

        except Exception as e:
            logger.error(f"Error getting jobs: {str(e)}")
            return []

    def search_jobs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search jobs with optional filters"""
        try:
            where_clauses = []

            if filters:
                if 'tech_id' in filters:
                    where_clauses.append(f"UPPER(techid) = UPPER('{filters['tech_id']}')")
                if 'job_status' in filters:
                    where_clauses.append(f"job_status = '{filters['job_status']}'")
                if 'job_type' in filters:
                    where_clauses.append(f"job_type = '{filters['job_type']}'")
                if 'job_date' in filters:
                    where_clauses.append(f"job_date = '{filters['job_date']}'")

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            sql = f"""
            SELECT *
            FROM {self.jobs_table}
            WHERE {where_clause}
            ORDER BY starttime ASC
            LIMIT 100
            """

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to search jobs: {result.get('message')}")
                return []

            jobs = []
            if 'result' in result and 'data_array' in result['result']:
                columns = [col['name'] for col in result['manifest']['schema']['columns']]

                for row in result['result']['data_array']:
                    job_data = dict(zip(columns, row))
                    jobs.append(job_data)

            logger.info(f"Found {len(jobs)} jobs matching filters")
            return jobs

        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []

    def has_active_current_job(self, tech_id: str, exclude_job_id: str = None) -> Optional[Dict[str, Any]]:
        """Check if tech has an active current job (Tech In Route, Tech On Site, or In Progress)"""
        try:
            sql = f"""
            SELECT *
            FROM {self.jobs_table}
            WHERE UPPER(techid) = UPPER('{tech_id}')
            AND jobstatus IN ('Tech In Route', 'Tech On Site', 'In Progress')
            """

            if exclude_job_id:
                sql += f" AND jobid != '{exclude_job_id}'"

            sql += " LIMIT 1"

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to check for active jobs: {result.get('message')}")
                return None

            if 'result' in result and 'data_array' in result['result'] and result['result']['data_array']:
                columns = [col['name'] for col in result['manifest']['schema']['columns']]
                active_job = dict(zip(columns, result['result']['data_array'][0]))
                logger.info(f"Found active current job: {active_job.get('jobid')}")
                return active_job

            return None

        except Exception as e:
            logger.error(f"Error checking for active jobs: {str(e)}")
            return None

    def update_job_status(self, job_id: str, new_status: str, tech_id: str = None) -> Dict[str, Any]:
        """Update job status for a specific job"""
        try:
            # Valid status values based on current data
            valid_statuses = ["Pending", "Tech In Route", "Tech On Site", "In Progress", "Completed", "Cancelled"]

            if new_status not in valid_statuses:
                return {
                    "success": False,
                    "message": f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}"
                }

            # Check if trying to start a new job while having an active current job
            if tech_id and new_status in ["Tech In Route", "Tech On Site", "In Progress"]:
                active_job = self.has_active_current_job(tech_id, exclude_job_id=job_id)
                if active_job:
                    return {
                        "success": False,
                        "message": f"Cannot start job {job_id}. You must complete your current job (Job ID: {active_job.get('jobid')}) before moving to the next job."
                    }

            sql = f"""
            UPDATE {self.jobs_table}
            SET jobstatus = '{new_status}'
            WHERE jobid = '{job_id}'
            """

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to update job status: {result.get('message')}")
                return {
                    "success": False,
                    "message": f"Failed to update job status: {result.get('message')}"
                }

            logger.info(f"Updated job {job_id} status to {new_status}")
            return {
                "success": True,
                "message": f"Job {job_id} status updated to {new_status}",
                "job_id": job_id,
                "new_status": new_status
            }

        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating job status: {str(e)}"
            }

    def format_jobs_for_display(self, jobs: List[Dict[str, Any]]) -> str:
        """Format job list for chatbot display"""
        if not jobs:
            return "No jobs found."

        output = ""

        for job in jobs:
            # Use Job ID as the header
            job_id = job.get('jobid', 'Unknown')
            output += f"{job_id}:\n"

            # Display drive time information if available (for next job)
            if 'drive_from_previous' in job:
                drive_info = job['drive_from_previous']
                output += f"  🚗 DRIVE TIME FROM PREVIOUS JOB:\n"
                output += f"     {drive_info['distance_miles']} miles • {drive_info['travel_time_minutes']} minutes\n"
                output += f"     From: {drive_info['from_address']}\n\n"

            # Display only requested fields
            if 'customername' in job:
                output += f"  • Customer Name: {job['customername']}\n"
            if 'phonenumber' in job:
                output += f"  • Phone: {job['phonenumber']}\n"
            if 'customeraddress' in job:
                output += f"  • Address: {job['customeraddress']}\n"
            if 'ordertype' in job:
                output += f"  • Order Type: {job['ordertype']}\n"
            if 'jobstatus' in job:
                output += f"  • Job Status: {job['jobstatus']}\n"
            if 'jobtype' in job:
                output += f"  • Job Type: {job['jobtype']}\n"

            output += "\n"

        return output.strip()

    def format_tech_info(self, tech_info: Dict[str, Any]) -> str:
        """Format tech info for display"""
        if not tech_info:
            return "Tech not found."

        output = "Technician Information:\n"

        if 'tech_id' in tech_info:
            output += f"  • Tech ID: {tech_info['tech_id']}\n"
        if 'tech_name' in tech_info:
            output += f"  • Name: {tech_info['tech_name']}\n"
        if 'tech_email' in tech_info:
            output += f"  • Email: {tech_info['tech_email']}\n"
        if 'tech_phone' in tech_info:
            output += f"  • Phone: {tech_info['tech_phone']}\n"
        if 'tech_skill_level' in tech_info:
            output += f"  • Skill Level: {tech_info['tech_skill_level']}\n"
        if 'tech_status' in tech_info:
            output += f"  • Status: {tech_info['tech_status']}\n"

        return output

    def get_equipment_needed(self, tech_id: str, date: str = None) -> List[Dict[str, Any]]:
        """Get equipment needed for a tech, optionally filtered by date"""
        try:
            # Note: Column name is 'equipment ' with trailing space
            sql = f"""
            SELECT `equipment `, type, SUM(CAST(qty AS INT)) as total_qty
            FROM {self.equipment_table}
            WHERE UPPER(techid) = UPPER('{tech_id}')
            """

            if date:
                sql += f" AND date = '{date}'"

            sql += """
            GROUP BY `equipment `, type
            ORDER BY `equipment ` ASC, type ASC
            """

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to get equipment: {result.get('message')}")
                return []

            equipment = []
            if 'result' in result and 'data_array' in result['result']:
                columns = [col['name'] for col in result['manifest']['schema']['columns']]

                for row in result['result']['data_array']:
                    equipment_data = dict(zip(columns, row))
                    equipment.append(equipment_data)

            logger.info(f"Found {len(equipment)} equipment types for tech {tech_id}")
            return equipment

        except Exception as e:
            logger.error(f"Error getting equipment: {str(e)}")
            return []

    def format_equipment_list(self, equipment: List[Dict[str, Any]]) -> str:
        """Format equipment list for chatbot display"""
        if not equipment:
            return "No equipment needed found."

        output = "Equipment Needed:\n\n"

        for item in equipment:
            # Column is 'equipment ' with trailing space
            equipment_name = item.get('equipment ', 'Unknown')
            equipment_type = item.get('type', '')
            qty = item.get('total_qty', 0)

            # Combine equipment name and type for display
            display_name = f"{equipment_name} ({equipment_type})" if equipment_type else equipment_name
            output += f"  • {display_name}: {qty}\n"

        return output.strip()


if __name__ == "__main__":
    # Test the module
    jobs_db = DatabricksJobs()

    print("=" * 80)
    print("DATABRICKS JOBS & TECHS MODULE TEST")
    print("=" * 80)
    print()

    # Test getting tech info
    test_tech_id = "TECH001"
    print(f"Testing with tech ID: {test_tech_id}")
    print()

    tech_info = jobs_db.get_tech_info(test_tech_id)
    if tech_info:
        print(jobs_db.format_tech_info(tech_info))
    else:
        print("Tech not found or table doesn't exist yet")
    print()

    # Test getting jobs
    jobs = jobs_db.get_jobs_for_tech(test_tech_id)
    print(jobs_db.format_jobs_for_display(jobs))
    print()

    print("=" * 80)
