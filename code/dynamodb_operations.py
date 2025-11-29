from datetime import datetime
from config import resumes_table, jobs_table, matches_table
import pandas as pd

def save_resume_to_dynamodb(resume_id, resume_data):
    """Save resume data to DynamoDB"""
    try:
        item = {
            'resumeId': resume_id,
            'uploadTimestamp': int(datetime.now().timestamp()),
            'name': resume_data.get('name', ''),
            'email': resume_data.get('email', ''),
            'phone': resume_data.get('phone', ''),
            'skills': resume_data.get('skills', ''),
            'cleanedText': resume_data.get('cleaned_text', ''),
            'rawText': resume_data.get('raw_text', ''),
            'createdAt': datetime.now().isoformat()
        }
        resumes_table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error saving to DynamoDB: {e}")
        return False

def get_all_resumes():
    """Get all resumes from DynamoDB"""
    try:
        response = resumes_table.scan()
        return pd.DataFrame(response.get('Items', []))
    except Exception as e:
        print(f"Error fetching resumes: {e}")
        return pd.DataFrame()

def save_job_to_dynamodb(job_id, job_data):
    """Save job description to DynamoDB"""
    try:
        item = {
            'jobId': job_id,
            'title': job_data.get('title', ''),
            'description': job_data.get('description', ''),
            'cleanedText': job_data.get('cleaned_text', ''),
            'createdAt': datetime.now().isoformat()
        }
        jobs_table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error saving job: {e}")
        return False

def get_all_jobs():
    """Get all jobs from DynamoDB"""
    try:
        response = jobs_table.scan()
        return pd.DataFrame(response.get('Items', []))
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return pd.DataFrame()

def save_match_result(match_id, resume_id, job_id, score, details):
    """Save match result"""
    try:
        item = {
            'matchId': match_id,
            'score': int(score * 100),  # Store as integer
            'resumeId': resume_id,
            'jobId': job_id,
            'details': details,
            'matchedAt': datetime.now().isoformat()
        }
        matches_table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error saving match: {e}")
        return False
