from io import BytesIO
import textract as tx
from config import s3_client, S3_BUCKET_RESUMES, S3_BUCKET_JOBS

def upload_file_to_s3(file_obj, bucket_name, file_key):
    """Upload file to S3"""
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, file_key)
        return f"s3://{bucket_name}/{file_key}"
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

def download_file_from_s3(bucket_name, file_key):
    """Download file from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        return response['Body'].read()
    except Exception as e:
        print(f"Error downloading from S3: {e}")
        return None

def list_files_in_s3(bucket_name, prefix=''):
    """List all files in S3 bucket with prefix"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            return []
        return [obj['Key'] for obj in response['Contents'] if not obj['Key'].endswith('/')]
    except Exception as e:
        print(f"Error listing S3 files: {e}")
        return []

def extract_text_from_s3_file(bucket_name, file_key):
    """Download file from S3 and extract text"""
    file_content = download_file_from_s3(bucket_name, file_key)
    if file_content:
        text = tx.process(BytesIO(file_content), encoding='ascii')
        return str(text, 'utf-8')
    return ""
