import boto3
import os

# S3 Configuration
S3_BUCKET_RESUMES = os.environ.get('S3_BUCKET_RESUMES', 'resume-matcher-resumes')
S3_BUCKET_JOBS = os.environ.get('S3_BUCKET_JOBS', 'resume-matcher-resumes')
S3_BUCKET_MODELS = os.environ.get('S3_BUCKET_MODELS', 'resume-matcher-models')

# DynamoDB Configuration
DYNAMODB_TABLE_RESUMES = os.environ.get('DYNAMODB_TABLE_RESUMES', 'ResumesTable')
DYNAMODB_TABLE_JOBS = os.environ.get('DYNAMODB_TABLE_JOBS', 'JobsTable')
DYNAMODB_TABLE_MATCHES = os.environ.get('DYNAMODB_TABLE_MATCHES', 'MatchResultsTable')


# SageMaker Configuration
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'spacy-endpoint')

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sagemaker_runtime = boto3.client('sagemaker-runtime')
