import os
import textract as tx
import Cleaner
import tf_idf
import boto3
from io import BytesIO
from config import S3_BUCKET_RESUMES, S3_BUCKET_JOBS, s3_client

resume_dir = "Data/Resumes/"
job_desc_dir = "Data/JobDesc/"

resume_names = os.listdir(resume_dir)
job_description_names = os.listdir(job_desc_dir)


def read_files_from_s3(bucket_name, prefix=''):
    """Read all files from S3 bucket"""
    placeholder = []
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if 'Contents' not in response:
        return placeholder

    for obj in response['Contents']:
        key = obj['Key']
        if key.endswith('/'):
            continue

        temp = [key.split('/')[-1]]
        file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        file_content = file_obj['Body'].read()

        # Process with textract
        text = tx.process(BytesIO(file_content), encoding='ascii')
        temp.append(str(text, 'utf-8'))
        placeholder.append(temp)

    return placeholder


def upload_file_to_s3(file_obj, bucket_name, file_name):
    """Upload file to S3 bucket"""
    s3_client.upload_fileobj(file_obj, bucket_name, file_name)
    return f"s3://{bucket_name}/{file_name}"


def read_files(list_of_resumes, resume_directory):
    """
        this function is to read all the files in the give directory
    """
    placeholder = []
    for res in list_of_resumes:
        if res == ".DS_Store":
            continue
        temp = [res]
        text = tx.process(resume_directory + res, encoding='ascii')
        text = str(text, 'utf-8')
        temp.append(text)
        placeholder.append(temp)
    return placeholder


def read_file(resumeName, resume_directory):
    """
        this function is to read a given file in the give directory
    """
    placeholder = []
    temp = [resumeName]
    text = tx.process(resume_directory + resumeName, encoding='ascii')
    temp.append(str(text, 'utf-8'))
    placeholder.append(temp)
    return placeholder


def get_cleaned_words(document, tfidf=False):
    """
        this function is to preprocess the texts
    """
    for content in document:
        raw = Cleaner.Cleaner(content[1])
        for processed in raw:
            content.append(" ".join(processed))
        if tfidf:
            content.append(content[3])
        else:
            sentence = tf_idf.do_tfidf(content[3].split(" "))
            content.append(sentence)
    return document
