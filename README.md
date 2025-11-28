# Cloud-Project
## Culling Resumes for jobs using NLP Techniques

### Table of contents:

- [Project Overview](#-Project-Overview)
- [Architecture](#-Architecture)
- [Architecture Diagram](#-Architecture-Diagram)
- [Data Flow](#-Data-Flow)
- [Technology Stack](#-Technology-Stack)
- [Security](#-Security)
- [Screenshots](#-Screenshots)
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


![cloud architecture diagram](https://github.com/user-attachments/assets/f4bc1e14-a1cd-427d-b873-4775dbdbbe82)

*Architecture Workflow diagram*

### Data Flow

#### User Uploads Resume or Job Description:
-  When user interacts with the Streamlit app (ECS Fargate).
-  File gets uploaded through the web interface.
-  Streamlit sends the file to the appropriate S3 bucket.

#### S3 Triggers Lambda: 
- S3 upload event automatically triggers a Lambda function.
- Lambda receives File name and Bucket location

#### Lambda Extracts & Cleans Text:
- Lambda does the preprocessing
- Reads file from S3
- Extracts text
- Removes noise, stopwords, punctuation
- Tokenizes, lemmatizes
- Saves processed text

#### Lambda Stores Processed Output:
- Structured output is written to DynamoDB
-  Resume metadata and cleaned text are stored in ResumesTable
- Job descriptions are stored in JobsTable 
- If matching is triggered, the results are stored in MatchResultsTable

#### Streamlit App Loads Processed Data:

- When user selects “Match Resumes”:
Streamlit reads cleaned resumes and job description from DynamoDB.

#### Ranked Results Returned to UI:

- Streamlit shows ranked list of candidates to the user.
- Optionally stores match results in DynamoDB.


### Technology Stack

#### Frontend:

- Amazon S3 + CloudFront: HTML, react frontend as static files in S3.
- CloudFront CDN ensures fast and secure content delivery globally.
- Amazon Route 53: Handles the custom domain and HTTPS routing

#### Backend:

- API Gateway: Serves as the entry point for frontend requests (like uploading resumes or viewing ranked results).
- AWS Lambda (Serverless) or Amazon EC2: Hosts backend logic — user authentication, job posting, fetching results, etc.
- AWS RDS (PostgreSQL/MySQL) or DynamoDB: Stores user data, job descriptions, and ranked candidate scores.

#### Machine Learning & NLP Pipeline:

- Amazon S3: Stores uploaded resumes (PDF/DOCX) and processed text data.
- Vectorization : TF - IDF(scikit-learn) for keyword weighting and BERT (HuggingFace Transformers) for semantic embeddings.
- Data Handling: NumPy and  Pandas to manipulate extracted text and embeddings.





