import boto3
import json
from config import SAGEMAKER_ENDPOINT, sagemaker_runtime

def invoke_sagemaker_endpoint(text):
    """Invoke SageMaker endpoint for NLP processing"""
    payload = json.dumps({'text': text})
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=payload
    )
    result = json.loads(response['Body'].read().decode())
    return result
