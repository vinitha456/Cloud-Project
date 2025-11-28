# Cloud-Project
## Culling Resumes for jobs using NLP Techniques

### Table of contents:

- [Project Overview](#-Project-Overview)
- [Architecture](#-Architecture)
- [Architecture Diagram](#-Architecture-Diagram)
- [Screenshots](#-Screenshots)
- [API Endpoints](#-API-Endpoints)
- [Data Flow](#-Data-Flow)
- [Technology Stack](#-Technology-Stack)
- [Security](#-Security)
- [Limitations](#-Limitations)

### Project Overview
This project delivers an automated resume matching system that uses NLP and machine learning to streamline the recruitment process. The system extracts key information from unstructured resumes, cleans and standardizes the content.The entire application is deployed on AWS using a scalable, serverless architecture with ECS Fargate, Lambda, S3, DynamoDB, and an Application Load Balancer, ensuring high availability, automated processing, and seamless updates through an EventBridge.
Extracts skills, experience, education, etc. from resumes using NLP

- Cleans and summarizes the resumes
- Converts resumes and job descriptions into vectors using BERT embeddings
- Compares them using cosine similarity
- Ranks candidates based on match score

### Architecture
The system uses a fully serverless, containerized architecture on AWS.

- User uploads a resume or job description via the Streamlit web UI.
- Files land in S3 (separate buckets for resumes and job descriptions).
- S3 event triggers a Lambda function on new uploads.
- Lambda extracts & cleans text.
- Lambda writes metadata and processed text to DynamoDB (ResumesTable, JobsTable, MatchResultsTable).
- Streamlit app (ECS Fargate) reads data from S3 or DynamoDB and loads the ML components.
- Matching engine produces embeddings and computes cosine similarity to rank candidates.
- ALB routes external traffic to Fargate tasks across multiple AZs for high availability.
- ECR stores Docker images; EventBridge watches for new image pushes and triggers a Lambda to force ECS rolling updates (zero-downtime deploys).
- CloudWatch Alarms collect logs, metrics, and alert on failures or resource issues.
- Security & networking: everything runs inside a VPC with private or public subnets, security groups and least-privilege IAM roles.


