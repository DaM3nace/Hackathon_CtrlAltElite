from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import uuid
from pathlib import Path
from simple_rag_system import SimpleRAGSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Knowledge Base Web Chat")

# Geocoding function using Nominatim (OpenStreetMap)
def geocode_address(address, city, state):
    """Geocode an address using Nominatim API"""
    try:
        # Build full address string
        full_address = f"{address}, {city}, {state}"

        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/search"

        # Parameters for the request
        params = {
            'q': full_address,
            'format': 'json',
            'limit': 1
        }

        # User agent is required by Nominatim
        headers = {
            'User-Agent': 'ChatBuddyClaude/1.0'
        }

        # Make request with timeout
        import requests as req_lib
        response = req_lib.get(url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                logger.info(f"Geocoded '{full_address}' to ({lat}, {lon})")
                return lat, lon

        logger.warning(f"Could not geocode address: {full_address}")
        return None, None

    except Exception as e:
        logger.error(f"Geocoding error for '{address}': {str(e)}")
        return None, None

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory="templates")

# Initialize RAG system
rag_system = SimpleRAGSystem()

# Store chat history per session (in production, use a database)
session_chats = {}

# Store tech authentication per session
session_tech_info = {}

@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request, session_id: str = Cookie(None)):
    # Create session if doesn't exist
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in session_chats:
        session_chats[session_id] = []

    # Check if tech is authenticated
    tech_authenticated = session_id in session_tech_info and session_tech_info[session_id] is not None
    tech_info = session_tech_info.get(session_id, None)

    stats = rag_system.get_knowledge_base_stats()

    response = templates.TemplateResponse("chat.html", {
        "request": request,
        "chat_history": session_chats[session_id],
        "stats": stats,
        "session_id": session_id,
        "tech_authenticated": tech_authenticated,
        "tech_info": tech_info
    })

    # Set session cookie
    response.set_cookie("session_id", session_id, max_age=86400)  # 24 hours
    return response

@app.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, question: str = Form(...), session_id: str = Cookie(None)):
    # Create session if doesn't exist
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if session_id not in session_chats:
        session_chats[session_id] = []
    
    if question.strip():
        try:
            # Check if question is about tech's personal info or jobs
            tech_info = session_tech_info.get(session_id, None)
            question_lower = question.lower()

            # Check for personal info queries
            is_personal_query = any(keyword in question_lower for keyword in [
                'my tech id', 'my id', 'who am i', 'my name', 'my info',
                'my information', 'my state', 'what is my'
            ])

            # Check for job status update queries
            is_status_update = any(keyword in question_lower for keyword in [
                'update status', 'change status', 'set status', 'mark job', 'complete job',
                'start job', 'cancel job', 'update job'
            ])

            # Also check for update with positional references (next/current/first job)
            if not is_status_update and 'update' in question_lower:
                if any(pos_ref in question_lower for pos_ref in ['next job', 'current job', 'first job']):
                    is_status_update = True
                    logger.info(f"Detected status update with positional reference")

            # Check for job queries
            is_job_query = any(keyword in question_lower for keyword in [
                'my jobs', 'my job', 'my schedule', 'my appointments', 'my appointment',
                'my work', 'what jobs', 'jobs do i have', 'jobs i have', 'jobs today',
                'jobs for today', 'my tasks', 'my assignments', 'order type', 'order types',
                'job order', 'job orders', 'what order', 'job type', 'customer name',
                'phone number', 'job address', 'job location', 'job city', 'job state',
                'start time', 'end time', 'duration', 'first job', 'next job', 'last job',
                'second job', 'third job', 'fourth job', 'fifth job', 'current job',
                'job customer', 'job phone', 'where is my', 'when is my', 'what time',
                'show map', 'display map', 'map of jobs', 'jobs on map', 'job map', 'show all jobs'
            ])

            # Check for help queries
            is_help_query = any(keyword in question_lower for keyword in [
                'help', 'what can i ask', 'what can you do', 'commands', 'options',
                'how to use', 'guide', 'instructions', 'what do you know', 'capabilities',
                'available commands', 'show commands', 'list commands'
            ])

            if is_help_query and tech_info:
                answer = """Available Commands:

📋 JOB QUERIES:
  • "Show my jobs" - View all your assigned jobs
  • "What is my next job?" - See your next pending job with drive time
  • "Show my current job" - View job currently in progress
  • "What is the order type for job 9012?" - Get specific job details
  • "Show all jobs on map" - Display all jobs on an interactive map

🔧 EQUIPMENT:
  • "What items do I need?" - View all equipment needed
  • "What equipment do I need today?" - Equipment for specific date

✏️ STATUS UPDATES:
  • "Update job 9012 to Completed" - Update specific job status
  • "Update next job to In Progress" - Auto-select next job
  • Valid statuses: Pending, Tech In Route, Tech On Site, In Progress, Completed, Cancelled

👤 PERSONAL INFO:
  • "What is my tech ID?" - View your technician information
  • "Who am I?" - See your profile details

📚 KNOWLEDGE BASE:
  • Ask questions about procedures, policies, and SOPs
  • Example: "How do I install an ONT?"
  • Example: "What are the safety procedures?"
"""

                # Add help response to chat history
                session_chats[session_id].append({
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "conversation_id": None,
                    "response_time_ms": 0
                })

            # Check for equipment queries
            elif is_equipment_query and tech_info:
                # Handle equipment query
                if rag_system.jobs_module:
                    try:
                        import re
                        from datetime import datetime

                        tech_id = tech_info.get('techid')

                        # Try to extract date from question (format: YYYY-MM-DD or common date phrases)
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', question)
                        date = None

                        if date_match:
                            date = date_match.group(0)
                        elif 'today' in question_lower:
                            date = datetime.now().strftime('%Y-%m-%d')

                        # Get equipment needed
                        equipment = rag_system.jobs_module.get_equipment_needed(tech_id, date)

                        if equipment:
                            answer = rag_system.jobs_module.format_equipment_list(equipment)
                        else:
                            if date:
                                answer = f"No equipment needed found for date {date}."
                            else:
                                answer = "No equipment needed found."

                    except Exception as e:
                        logger.error(f"Error getting equipment: {str(e)}")
                        answer = f"Error retrieving equipment information: {str(e)}"
                else:
                    answer = "Equipment information is not available at this time."

                # Add equipment query result to chat history
                session_chats[session_id].append({
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "conversation_id": None,
                    "response_time_ms": 0
                })
            elif is_status_update and tech_info:
                # Handle job status update
                if rag_system.jobs_module:
                    try:
                        import re
                        # Try to extract job ID and new status from the question
                        # Patterns: "update job 9012 to Completed", "mark job 9012 as In Progress", etc.
                        job_match = re.search(r'\b(\d{4})\b', question)  # Find 4-digit job ID
                        logger.info(f"Status update request - Question: '{question}'")
                        logger.info(f"Job ID match: {job_match.group(1) if job_match else 'None'}")

                        # Status mapping for natural language
                        status_keywords = {
                            'pending': 'Pending',
                            'tech in route': 'Tech In Route',
                            'in route': 'Tech In Route',
                            'en route': 'Tech In Route',
                            'on the way': 'Tech In Route',
                            'on site': 'Tech On Site',
                            'tech on site': 'Tech On Site',
                            'onsite': 'Tech On Site',
                            'in progress': 'In Progress',
                            'started': 'In Progress',
                            'working': 'In Progress',
                            'completed': 'Completed',
                            'complete': 'Completed',
                            'done': 'Completed',
                            'finished': 'Completed',
                            'cancelled': 'Cancelled',
                            'canceled': 'Cancelled',
                            'cancel': 'Cancelled'
                        }

                        new_status = None
                        # Sort by keyword length (longest first) to match multi-word phrases first
                        sorted_keywords = sorted(status_keywords.items(), key=lambda x: len(x[0]), reverse=True)
                        for keyword, status in sorted_keywords:
                            if keyword in question_lower:
                                new_status = status
                                logger.info(f"Matched status keyword '{keyword}' -> '{status}'")
                                break

                        # If no job ID found, check for positional references (next, current, first)
                        job_id = None
                        if job_match:
                            job_id = job_match.group(1)
                        elif not job_match:
                            # Check for positional job references
                            tech_id = tech_info.get('techid')
                            jobs = rag_system.jobs_module.get_jobs_for_tech(tech_id)

                            if 'current' in question_lower:
                                # Find current job (Tech In Route, Tech On Site, or In Progress)
                                current_jobs = [j for j in jobs if j.get('jobstatus') in ['Tech In Route', 'Tech On Site', 'In Progress']]
                                if current_jobs:
                                    job_id = str(current_jobs[0].get('jobid'))
                                    logger.info(f"Found current job: {job_id}")
                            elif 'next' in question_lower:
                                # Find next job (first Pending job)
                                pending_jobs = [j for j in jobs if j.get('jobstatus') == 'Pending']
                                if pending_jobs:
                                    job_id = str(pending_jobs[0].get('jobid'))
                                    logger.info(f"Found next job: {job_id}")
                            elif 'first' in question_lower:
                                # First job in list
                                if jobs:
                                    job_id = str(jobs[0].get('jobid'))
                                    logger.info(f"Found first job: {job_id}")

                        if job_id and new_status:
                            # Get tech_id from session
                            tech_id = tech_info.get('techid')
                            result = rag_system.jobs_module.update_job_status(job_id, new_status, tech_id)

                            if result.get('success'):
                                answer = f"✓ Job {job_id} status updated to '{new_status}'. Customer has been notified."
                            else:
                                answer = f"Failed to update job status: {result.get('message', 'Unknown error')}"
                        elif job_id and not new_status:
                            # Auto-determine next status based on current status
                            tech_id = tech_info.get('techid')
                            jobs = rag_system.jobs_module.get_jobs_for_tech(tech_id)
                            current_job = next((j for j in jobs if str(j.get('jobid')) == job_id), None)

                            if current_job:
                                current_status = current_job.get('jobstatus', '')
                                # Define workflow progression
                                status_workflow = {
                                    'Pending': 'Tech In Route',
                                    'Tech In Route': 'Tech On Site',
                                    'Tech On Site': 'In Progress',
                                    'In Progress': 'Completed'
                                }

                                next_status = status_workflow.get(current_status)

                                if next_status:
                                    # Update to next status in workflow
                                    result = rag_system.jobs_module.update_job_status(job_id, next_status, tech_id)

                                    if result.get('success'):
                                        answer = f"✓ Job {job_id} status updated from '{current_status}' to '{next_status}'. Customer has been notified."
                                    else:
                                        answer = f"Failed to update job status: {result.get('message', 'Unknown error')}"
                                else:
                                    answer = f"Job {job_id} is currently '{current_status}'. Cannot automatically progress further. Please specify a status manually."
                            else:
                                answer = f"Could not find job {job_id} to determine current status."
                        else:
                            answer = "Please specify a job ID and status. Example: 'update job 9012 to Completed' or 'update next job to In Progress'"

                        session_chats[session_id].append({
                            "question": question,
                            "answer": answer,
                            "sources": [],
                            "conversation_id": None,
                            "response_time_ms": 0
                        })
                    except Exception as e:
                        logger.error(f"Error updating job status: {str(e)}")
                        session_chats[session_id].append({
                            "question": question,
                            "answer": f"Error updating job status: {str(e)}",
                            "sources": [],
                            "conversation_id": None,
                            "response_time_ms": 0
                        })
                else:
                    session_chats[session_id].append({
                        "question": question,
                        "answer": "Job status update system is not available",
                        "sources": [],
                        "conversation_id": None,
                        "response_time_ms": 0
                    })
            elif is_personal_query and tech_info:
                # Answer with tech's personal information
                tech_id = tech_info.get('techid', 'Unknown')
                firstname = tech_info.get('firstname', '')
                lastname = tech_info.get('lastname', '')
                state = tech_info.get('state', 'Unknown')

                answer = f"Your information:\n\n"
                answer += f"Tech ID: {tech_id}\n"
                answer += f"Name: {firstname} {lastname}\n"
                answer += f"State: {state}"

                session_chats[session_id].append({
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "conversation_id": None,
                    "response_time_ms": 0
                })
            elif is_job_query and tech_info:
                # Answer with tech's job information
                tech_id = tech_info.get('techid', 'Unknown')

                if rag_system.jobs_module:
                    try:
                        import re

                        # Get all jobs for the tech
                        jobs = rag_system.jobs_module.get_jobs_for_tech(tech_id)

                        # Detect if asking for a specific field
                        specific_field = None
                        field_patterns = {
                            'order type': 'ordertype',
                            'order-type': 'ordertype',
                            'ordertype': 'ordertype',
                            'job type': 'jobtype',
                            'job-type': 'jobtype',
                            'jobtype': 'jobtype',
                            'customer name': 'customername',
                            'customer': 'customername',
                            'phone': 'phonenumber',
                            'phone number': 'phonenumber',
                            'address': 'customeraddress',
                            'location': 'city',
                            'city': 'city',
                            'state': 'state',
                            'appointment': 'appointment',
                            'start time': 'starttime',
                            'end time': 'endtime',
                            'duration': 'durationhours'
                        }

                        # Check if asking "what is/are the X" or "show X" or "where is" or "when is"
                        for pattern, field in field_patterns.items():
                            if re.search(rf'\b(what is|what are|what\'s|show|tell me|get|where is|where are|when is|when are)\s+(the\s+|my\s+)?{pattern}\b', question_lower):
                                specific_field = field
                                logger.info(f"Detected field-specific query for: {field}")
                                break

                        # Also check for plural field references without verbs (e.g., "order types", "job types")
                        if not specific_field:
                            plural_patterns = {
                                'order types': 'ordertype',
                                'job types': 'jobtype',
                                'customer names': 'customername',
                                'phone numbers': 'phonenumber',
                                'addresses': 'customeraddress',
                                'cities': 'city',
                                'states': 'state',
                                'appointments': 'appointment',
                                'start times': 'starttime',
                                'end times': 'endtime',
                                'durations': 'durationhours'
                            }
                            for pattern, field in plural_patterns.items():
                                if pattern in question_lower:
                                    specific_field = field
                                    logger.info(f"Detected plural field reference for: {field}")
                                    break

                        # Also check for "where" or "located" queries for location fields
                        if not specific_field and re.search(r'\b(where|location|located|city|address)\b', question_lower):
                            if 'address' in question_lower:
                                specific_field = 'customeraddress'
                            else:
                                specific_field = 'city'  # Default to city for location queries
                            logger.info(f"Detected location query, using field: {specific_field}")

                        # Filter for specific items if mentioned in query
                        # Check for "current job" - jobs with status "Tech On Site", "Tech In Route", or "In Progress"
                        if 'current' in question_lower and 'job' in question_lower:
                            current_jobs = [j for j in jobs if j.get('jobstatus') in ['Tech On Site', 'Tech In Route', 'In Progress']]
                            if current_jobs:
                                jobs = current_jobs
                                logger.info(f"Filtered to current job(s) with status Tech On Site, Tech In Route, or In Progress: {len(current_jobs)} job(s)")
                            else:
                                logger.info("No current jobs found (Tech On Site, Tech In Route, or In Progress)")
                        # Check for positional job references (first, next, last)
                        elif 'first' in question_lower:
                            jobs = jobs[:1]  # Get only the first job
                            logger.info("Filtered to first job")
                        elif 'next' in question_lower:
                            # Filter to next job - first job with "Pending" status
                            all_jobs = jobs.copy()  # Keep all jobs for reference
                            pending_jobs = [j for j in jobs if j.get('jobstatus') == 'Pending']
                            if pending_jobs:
                                next_job = pending_jobs[0]  # Get the first pending job
                                jobs = [next_job]
                                logger.info(f"Filtered to next job (first Pending job, found {len(pending_jobs)} pending jobs)")

                                # Find previous job (current or last completed job)
                                prev_job = None
                                for job in all_jobs:
                                    status = job.get('jobstatus', '')
                                    # Current job
                                    if status in ['Tech In Route', 'Tech On Site', 'In Progress']:
                                        prev_job = job
                                        break

                                # If no current job, find last completed job
                                if not prev_job:
                                    completed_jobs = [j for j in all_jobs if j.get('jobstatus') == 'Completed']
                                    if completed_jobs:
                                        prev_job = completed_jobs[-1]  # Get the last completed job

                                # Calculate drive time if we have both jobs with addresses
                                if prev_job:
                                    prev_addr = prev_job.get('customeraddress', '')
                                    prev_city = prev_job.get('city', '')
                                    prev_state = prev_job.get('state', '')
                                    next_addr = next_job.get('customeraddress', '')
                                    next_city = next_job.get('city', '')
                                    next_state = next_job.get('state', '')

                                    if prev_addr and prev_city and prev_state and next_addr and next_city and next_state:
                                        # Geocode both addresses
                                        prev_lat, prev_lng = geocode_address(prev_addr, prev_city, prev_state)
                                        next_lat, next_lng = geocode_address(next_addr, next_city, next_state)

                                        if prev_lat and prev_lng and next_lat and next_lng:
                                            # Calculate distance using Haversine formula
                                            from math import radians, sin, cos, sqrt, atan2
                                            R = 3959  # Earth's radius in miles

                                            lat1, lng1 = radians(prev_lat), radians(prev_lng)
                                            lat2, lng2 = radians(next_lat), radians(next_lng)

                                            dlat = lat2 - lat1
                                            dlng = lng2 - lng1

                                            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
                                            c = 2 * atan2(sqrt(a), sqrt(1-a))
                                            distance = R * c

                                            # Estimate travel time (35 mph average)
                                            travel_time_minutes = (distance / 35) * 60

                                            # Store in next job for display
                                            next_job['drive_from_previous'] = {
                                                'distance_miles': round(distance, 1),
                                                'travel_time_minutes': round(travel_time_minutes),
                                                'from_address': f"{prev_addr}, {prev_city}, {prev_state}"
                                            }
                                            logger.info(f"Calculated drive time: {distance:.1f} miles, {travel_time_minutes:.0f} minutes")
                            else:
                                jobs = jobs[:1]  # Fallback to first job if no pending jobs
                                logger.info("No pending jobs found, showing first job")
                        elif 'last' in question_lower:
                            jobs = jobs[-1:]  # Get only the last job
                            logger.info("Filtered to last job")
                        elif 'second' in question_lower:
                            if len(jobs) >= 2:
                                jobs = [jobs[1]]  # Get the second job (index 1)
                                logger.info("Filtered to second job")
                            else:
                                logger.info(f"Only {len(jobs)} job(s) available, cannot get second job")
                        elif 'third' in question_lower:
                            if len(jobs) >= 3:
                                jobs = [jobs[2]]  # Get the third job (index 2)
                                logger.info("Filtered to third job")
                            else:
                                logger.info(f"Only {len(jobs)} job(s) available, cannot get third job")
                        elif 'fourth' in question_lower:
                            if len(jobs) >= 4:
                                jobs = [jobs[3]]  # Get the fourth job (index 3)
                                logger.info("Filtered to fourth job")
                            else:
                                logger.info(f"Only {len(jobs)} job(s) available, cannot get fourth job")
                        elif 'fifth' in question_lower:
                            if len(jobs) >= 5:
                                jobs = [jobs[4]]  # Get the fifth job (index 4)
                                logger.info("Filtered to fifth job")
                            else:
                                logger.info(f"Only {len(jobs)} job(s) available, cannot get fifth job")

                        # Check for specific job ID (4+ digit numbers)
                        job_id_match = re.search(r'\b(\d{4,})\b', question)
                        if job_id_match:
                            job_id = job_id_match.group(1)
                            jobs = [j for j in jobs if str(j.get('jobid', '')) == job_id]
                            logger.info(f"Filtered to specific job ID: {job_id}")

                        # Check for specific order type
                        order_type_match = re.search(r'order\s+type\s+["\']?(\w+)["\']?', question_lower)
                        if order_type_match:
                            order_type = order_type_match.group(1).upper()
                            jobs = [j for j in jobs if j.get('ordertype', '').upper() == order_type]
                            logger.info(f"Filtered to specific order type: {order_type}")

                        # Check for specific job type
                        job_type_keywords = ['install', 'repair', 'maintenance', 'upgrade', 'disconnect']
                        for keyword in job_type_keywords:
                            if keyword in question_lower and 'job type' in question_lower:
                                jobs = [j for j in jobs if keyword.lower() in j.get('jobtype', '').lower()]
                                logger.info(f"Filtered to job type containing: {keyword}")
                                break

                        # Check for specific customer name
                        customer_match = re.search(r'customer\s+["\']?([a-zA-Z\s]+)["\']?', question_lower)
                        if customer_match:
                            customer_name = customer_match.group(1).strip()
                            jobs = [j for j in jobs if customer_name.lower() in j.get('customername', '').lower()]
                            logger.info(f"Filtered to customer: {customer_name}")

                        # Geocode job addresses for map display (only if not showing a single specific field)
                        job_locations = []
                        if not specific_field and jobs:
                            for job in jobs:
                                address = job.get('customeraddress', '')
                                city = job.get('city', '')
                                state = job.get('state', '')

                                if address and city and state:
                                    lat, lng = geocode_address(address, city, state)
                                    if lat and lng:
                                        job_locations.append({
                                            'lat': lat,
                                            'lng': lng,
                                            'customername': job.get('customername', 'Unknown'),
                                            'address': address,
                                            'city': city,
                                            'state': state,
                                            'jobtype': job.get('jobtype', ''),
                                            'ordertype': job.get('ordertype', ''),
                                            'appointment': job.get('appointment', '')
                                        })

                        # Store job locations in session for rendering
                        if session_id not in session_chats:
                            session_chats[session_id] = []

                        # Format answer based on whether specific field was requested
                        if specific_field and jobs:
                            # Only show the specific field
                            field_label_map = {
                                'ordertype': 'Order Type',
                                'jobtype': 'Job Type',
                                'customername': 'Customer',
                                'phonenumber': 'Phone',
                                'customeraddress': 'Address',
                                'city': 'City',
                                'state': 'State',
                                'appointment': 'Appointment',
                                'starttime': 'Start Time',
                                'endtime': 'End Time',
                                'durationhours': 'Duration'
                            }

                            field_label = field_label_map.get(specific_field, specific_field)

                            if len(jobs) == 1:
                                value = jobs[0].get(specific_field, 'N/A')
                                if specific_field == 'durationhours':
                                    answer = f"{field_label}: {value} hour(s)"
                                else:
                                    answer = f"{field_label}: {value}"
                            else:
                                answer = f"Found {len(jobs)} job(s). {field_label} values:\n\n"
                                for i, job in enumerate(jobs, 1):
                                    value = job.get(specific_field, 'N/A')
                                    job_id = job.get('jobid', 'Unknown')
                                    if specific_field == 'durationhours':
                                        answer += f"Job {job_id}: {value} hour(s)\n"
                                    else:
                                        answer += f"Job {job_id}: {value}\n"
                        else:
                            # Show full job details
                            answer = rag_system.jobs_module.format_jobs_for_display(jobs)
                    except Exception as e:
                        logger.error(f"Error getting jobs: {str(e)}")
                        answer = f"Error retrieving your jobs: {str(e)}"
                else:
                    answer = "Job information system is not available."

                session_chats[session_id].append({
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "conversation_id": None,
                    "response_time_ms": 0
                })
            else:
                result = rag_system.ask_question(question, top_k=3, session_id=session_id)

                session_chats[session_id].append({
                    "question": question,
                    "answer": result["response"],
                    "sources": result["sources"],
                    "conversation_id": result["conversation_id"],
                    "response_time_ms": result["response_time_ms"]
                })

            # Keep only last 20 conversations per session
            if len(session_chats[session_id]) > 20:
                session_chats[session_id].pop(0)

        except Exception as e:
            session_chats[session_id].append({
                "question": question,
                "answer": f"Error: {str(e)}",
                "sources": [],
                "conversation_id": None,
                "response_time_ms": 0
            })
    
    stats = rag_system.get_knowledge_base_stats()

    # Check if tech is authenticated
    tech_authenticated = session_id in session_tech_info and session_tech_info[session_id] is not None
    tech_info = session_tech_info.get(session_id, None)

    # Get job locations if they were geocoded in this request
    template_context = {
        "request": request,
        "chat_history": session_chats[session_id],
        "stats": stats,
        "session_id": session_id,
        "tech_authenticated": tech_authenticated,
        "tech_info": tech_info
    }

    # Add job_locations to context if available (from local scope)
    if 'job_locations' in locals() and job_locations:
        template_context["job_locations"] = job_locations
        logger.info(f"Passing {len(job_locations)} job locations to template")

    response = templates.TemplateResponse("chat.html", template_context)

    # Set session cookie
    response.set_cookie("session_id", session_id, max_age=86400)
    return response

@app.post("/verify-tech", response_class=HTMLResponse)
async def verify_tech(request: Request, tech_id: str = Form(...), session_id: str = Cookie(None)):
    # Create session if doesn't exist
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in session_chats:
        session_chats[session_id] = []

    # Verify tech ID against Databricks
    tech_info = None
    error_message = None

    if rag_system.jobs_module:
        try:
            tech_info = rag_system.jobs_module.get_tech_info(tech_id.strip().upper())

            if tech_info:
                # Store tech info in session
                session_tech_info[session_id] = tech_info
                logger.info(f"Tech {tech_id} authenticated successfully")
            else:
                error_message = f"Tech ID '{tech_id}' not found. Please try again."
                logger.warning(f"Tech ID {tech_id} not found")
        except Exception as e:
            error_message = f"Error verifying tech ID: {str(e)}"
            logger.error(f"Error verifying tech: {str(e)}")
    else:
        error_message = "Tech verification system is not available"

    stats = rag_system.get_knowledge_base_stats()

    response = templates.TemplateResponse("chat.html", {
        "request": request,
        "chat_history": session_chats[session_id],
        "stats": stats,
        "session_id": session_id,
        "tech_authenticated": tech_info is not None,
        "tech_info": tech_info,
        "tech_error": error_message
    })

    # Set session cookie
    response.set_cookie("session_id", session_id, max_age=86400)
    return response

@app.post("/clear")
async def clear_chat(session_id: str = Cookie(None)):
    if session_id and session_id in session_chats:
        session_chats[session_id] = []
    return {"status": "cleared"}

@app.get("/stats")
async def get_stats():
    return rag_system.get_knowledge_base_stats()

@app.post("/update-job-status")
async def update_job_status(request: Request, session_id: str = Cookie(None)):
    """Update job status endpoint"""
    try:
        # Check if tech is authenticated
        if not session_id or session_id not in session_tech_info:
            return {"success": False, "message": "Tech not authenticated"}

        # Parse JSON body
        data = await request.json()
        job_id = data.get('job_id')
        new_status = data.get('new_status')

        if not job_id or not new_status:
            return {"success": False, "message": "Missing job_id or new_status"}

        # Update job status via jobs module
        if rag_system.jobs_module:
            result = rag_system.jobs_module.update_job_status(job_id, new_status)
            return result
        else:
            return {"success": False, "message": "Jobs module not available"}

    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)