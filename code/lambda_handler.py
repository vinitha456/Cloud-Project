import json
import boto3
import textract as tx
from io import BytesIO

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    # Get S3 event details
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Download file from S3
        file_obj = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = file_obj['Body'].read()

        # Extract text
        text = tx.process(BytesIO(file_content), encoding='ascii')
        extracted_text = str(text, 'utf-8')

        # Store in DynamoDB
        table = dynamodb.Table('ResumesTable')
        table.put_item(Item={
            'resumeId': key,
            'rawText': extracted_text,
            'uploadTimestamp': int(record['eventTime'])
        })

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }
