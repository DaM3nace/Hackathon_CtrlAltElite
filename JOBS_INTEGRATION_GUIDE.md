# Tech Jobs Integration Guide

## Overview

The chatbot now integrates with Databricks `jobs` and `techs` tables to look up technician job schedules.

## How to Use

### Query Examples

Ask the chatbot about tech jobs using natural language. The system will automatically detect job queries and route them to the jobs module.

**Example Queries:**

1. "Show jobs for TECH001"
2. "What are the jobs for tech123?"
3. "List appointments for TECH005"
4. "Get schedule for technician TECH042"
5. "Show me tech jobs for T001"

### Tech ID Formats Supported

- `TECH001`, `TECH123` (uppercase TECH followed by numbers)
- `tech001`, `tech123` (lowercase tech followed by numbers)
- `T001`, `T0001` (T followed by 3+ numbers)

### Response Format

The chatbot will return:

1. **Technician Information** (if found):
   - Tech ID
   - Name
   - Email
   - Phone
   - Skill Level
   - Status

2. **Job List**:
   - Job ID
   - Job Type
   - Date
   - Time
   - Customer Name
   - Address
   - Status
   - Description

## Database Tables

### Tables Used

- `hackathon.hackathon_ctrl_alt_elite.jobs` - Job records
- `hackathon.hackathon_ctrl_alt_elite.techs` - Technician information

### Required Table Schema

**techs table** should have columns like:
- `tech_id` (string) - Unique tech identifier
- `tech_name` (string) - Technician name
- `tech_email` (string) - Email address
- `tech_phone` (string) - Phone number
- `tech_skill_level` (string) - Skill level
- `tech_status` (string) - Active/Inactive status

**jobs table** should have columns like:
- `job_id` (string) - Unique job identifier
- `tech_id` (string) - Assigned technician ID
- `job_type` (string) - Type of job
- `job_date` (date) - Job date
- `job_time` (time) - Job time
- `customer_name` (string) - Customer name
- `address` (string) - Job address
- `job_status` (string) - Status (scheduled, in progress, completed, etc.)
- `job_description` (string) - Job details

## How It Works

### 1. Query Detection

The system detects job queries by looking for:
- Job-related keywords: `job`, `jobs`, `schedule`, `appointment`, `work order`, `assignment`, `task`, `ticket`, `service call`
- Tech-related keywords: `tech`, `technician`, `my jobs`, `my schedule`, `my appointments`
- Or presence of a Tech ID pattern

### 2. Tech ID Extraction

The system extracts the tech ID from the query using regex patterns.

### 3. Database Lookup

- Queries the `techs` table for technician information
- Queries the `jobs` table for all jobs assigned to that tech ID
- Orders jobs by date and time (most recent first)

### 4. Response Formatting

Formats the results in a readable format and returns to the user.

## Code Components

### Files Created/Modified

1. **databricks_jobs.py** - New module for job queries
   - `DatabricksJobs` class
   - Methods: `get_tech_info()`, `get_jobs_for_tech()`, `search_jobs()`

2. **simple_rag_system.py** - Modified to integrate jobs
   - `extract_tech_id()` - Extract tech ID from query
   - `is_job_query()` - Detect if query is about jobs
   - `handle_job_query()` - Process job queries
   - Updated `ask_question()` - Route to jobs module when needed

### Conversation Logging

Job queries are logged in the conversation history with:
- `query_type`: "job_lookup"
- `tech_id`: The technician ID queried
- `job_count`: Number of jobs found
- `model_used`: "databricks_jobs"

## Testing

### Test the Jobs Module

```bash
python databricks_jobs.py
```

This will test queries against the jobs and techs tables.

### Test Through Chatbot

1. Visit http://127.0.0.1:8000
2. Type: "Show jobs for TECH001"
3. System should return tech info and job list

### If Tables Don't Exist Yet

The chatbot will handle gracefully and inform the user that tables need to be created.

## Error Handling

- **Tech ID not provided**: Returns message asking for tech ID
- **Tech not found**: Returns message indicating tech ID not in system
- **No jobs found**: Returns "No jobs found" message
- **Database error**: Logs error and returns user-friendly message

## Future Enhancements

Possible improvements:
- Filter jobs by status, date range, job type
- Search jobs by customer name or address
- Update job status
- Create new job assignments
- View job history and metrics
- Schedule optimization

## Configuration

The jobs integration uses the same Databricks configuration as the rest of the system:
- `DATABRICKS_SERVER_HOSTNAME`
- `DATABRICKS_HTTP_PATH`
- `DATABRICKS_TOKEN`
- `DATABRICKS_CATALOG`
- `DATABRICKS_SCHEMA`

Table names are constructed as:
- `{catalog}.{schema}.jobs`
- `{catalog}.{schema}.techs`

---

**Status**: ✅ Integrated and Running

**Chatbot**: http://127.0.0.1:8000 (Process 16704)
