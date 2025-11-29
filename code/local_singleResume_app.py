import tempfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
import base64
import uuid
from datetime import datetime

# AWS Integration imports
import boto3
import os

# Local imports
import Similar
from info_extractor import *

# ========================= AWS Configuration =========================
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
S3_BUCKET_RESUMES = os.environ.get('S3_BUCKET_RESUMES', 'resume-matcher-resumes')
S3_BUCKET_JOBS = os.environ.get('S3_BUCKET_JOBS', 'resume-matcher-resumes')
DYNAMODB_TABLE_RESUMES = os.environ.get('DYNAMODB_TABLE_RESUMES', 'ResumesTable')
DYNAMODB_TABLE_JOBS = os.environ.get('DYNAMODB_TABLE_JOBS', 'JobsTable')
DYNAMODB_TABLE_MATCHES = os.environ.get('DYNAMODB_TABLE_MATCHES', 'MatchResultsTable')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'AKIAWPBN7XALMMWOKYBZ')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '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')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
resumes_table = dynamodb.Table(DYNAMODB_TABLE_RESUMES)
jobs_table = dynamodb.Table(DYNAMODB_TABLE_JOBS)
matches_table = dynamodb.Table(DYNAMODB_TABLE_MATCHES)

# Load spaCy model
nlp = spacy.load("en_core_web_md")


# ========================= AWS Helper Functions =========================
def upload_file_to_s3(file_obj, bucket_name, file_key):
    """Upload file to S3"""
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, file_key)
        return f"s3://{bucket_name}/{file_key}"
    except Exception as e:
        st.error(f"Error uploading to S3: {e}")
        return None


def bulk_upload_to_s3(uploaded_files, bucket_name, prefix='jobs/'):
    """Upload multiple files to S3"""
    uploaded_count = 0
    failed_files = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, file in enumerate(uploaded_files):
        try:
            file_key = f"{prefix}{uuid.uuid4()}_{file.name}"
            s3_client.upload_fileobj(file, bucket_name, file_key)
            uploaded_count += 1

            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Uploading {idx + 1}/{len(uploaded_files)}: {file.name}")

        except Exception as e:
            failed_files.append(file.name)
            st.warning(f"Failed to upload {file.name}: {e}")

    progress_bar.empty()
    status_text.empty()

    return uploaded_count, failed_files


def download_file_from_s3(bucket_name, file_key):
    """Download file from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        return response['Body'].read()
    except Exception as e:
        st.error(f"Error downloading from S3: {e}")
        return None


def list_files_in_s3(bucket_name, prefix=''):
    """List all files in S3 bucket with prefix"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            return []
        return [obj['Key'] for obj in response['Contents'] if not obj['Key'].endswith('/')]
    except Exception as e:
        st.error(f"Error listing S3 files: {e}")
        return []


def extract_text_from_s3_file(bucket_name, file_key):
    """Download file from S3 and extract text - FIXED VERSION"""
    try:
        import textract as tx

        # Download file content from S3
        file_content = download_file_from_s3(bucket_name, file_key)

        if not file_content:
            return ""

        # Get file extension from S3 key
        file_extension = os.path.splitext(file_key)[1]
        if not file_extension:
            file_extension = '.pdf'  # Default to PDF

        # Create a temporary file and write the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            temp_file_path = temp_file.name

        try:
            # Process the temporary file with textract
            text = tx.process(temp_file_path, encoding='ascii')
            extracted_text = str(text, 'utf-8')
            return extracted_text
        finally:
            # Always delete the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""

def process_bulk_jobs_from_s3(bucket_name, prefix='jobs/'):
    """Process all unprocessed job files from S3"""
    try:
        # Get all files from S3
        s3_files = list_files_in_s3(bucket_name, prefix)

        # Get already processed jobs from DynamoDB
        response = jobs_table.scan()
        processed_keys = [item.get('s3Key', '') for item in response.get('Items', [])]

        # Find unprocessed files
        unprocessed_files = [f for f in s3_files if f not in processed_keys]

        if not unprocessed_files:
            return 0

        processed_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file_key in enumerate(unprocessed_files):
            # try:
            status_text.text(f"Processing {idx + 1}/{len(unprocessed_files)}: {file_key.split('/')[-1]}")
            print("Done-1")
            # Extract text
            extracted_text = extract_text_from_s3_file(bucket_name, file_key)
            print("Done-2")
            if extracted_text:
                # Clean text
                cleaned_text = clean_text(extracted_text)
                print("Done-3")
                print(file_key.split('/')[-1],extracted_text,file_key)
                # Prepare job data
                job_data = {
                    'name': file_key.split('/')[-1],
                    'raw_text': extracted_text,
                    'cleaned_text': cleaned_text,
                    's3_key': file_key,
                    'description': extracted_text[:500]  # First 500 chars
                }
                print("Done-4")
                # Save to DynamoDB
                job_id = file_key.split('/')[-1]
                print("Done-5")
                if save_job_to_dynamodb(job_id, job_data):
                    print("Done-6")
                    processed_count += 1
            print("Done-7")
            progress = (idx + 1) / len(unprocessed_files)
            progress_bar.progress(progress)
            print("Done-8")
            # except Exception as e:
            #     st.warning(f"Failed to process {file_key}: {e}")

        progress_bar.empty()
        status_text.empty()

        return processed_count

    except Exception as e:
        st.error(f"Error processing bulk jobs: {e}")
        return 0


def save_resume_to_dynamodb(resume_id, resume_data):
    """Save resume data to DynamoDB"""
    try:
        item = {
            'resumeId': resume_id,
            'uploadTimestamp': str(datetime.now().timestamp()),
            'fileName': resume_data.get('name', ''),
            'email': resume_data.get('email', ''),
            'phone': resume_data.get('phone', ''),
            'cleanedText': resume_data.get('cleaned_text', ''),
            'rawText': resume_data.get('raw_text', ''),
            's3Key': resume_data.get('s3_key', ''),
            'createdAt': datetime.now().isoformat()
        }
        resumes_table.put_item(Item=item)
        return True
    except Exception as e:
        st.error(f"Error saving to DynamoDB: {e}")
        return False


def get_all_resumes():
    """Get all resumes from DynamoDB"""
    try:
        response = resumes_table.scan()
        items = response.get('Items', [])

        if items:
            df_data = {
                'Name': [item.get('fileName', '') for item in items],
                'Context': [item.get('rawText', '') for item in items],
                'Cleaned': [item.get('cleanedText', '') for item in items],
                'ID': [item.get('resumeId', '') for item in items]
            }
            return pd.DataFrame(df_data)
        return pd.DataFrame(columns=['Name', 'Context', 'Cleaned', 'ID'])
    except Exception as e:
        st.error(f"Error fetching resumes: {e}")
        return pd.DataFrame(columns=['Name', 'Context', 'Cleaned', 'ID'])


def save_job_to_dynamodb(job_id, job_data):
    """Save job description to DynamoDB"""
    try:
        item = {
            'jobId': job_id,
            'fileName': job_data.get('name', ''),
            'description': job_data.get('description', ''),
            'cleanedText': job_data.get('cleaned_text', ''),
            'rawText': job_data.get('raw_text', ''),
            's3Key': job_data.get('s3_key', ''),
            'createdAt': datetime.now().isoformat()
        }
        jobs_table.put_item(Item=item)
        return True
    except Exception as e:
        st.error(f"Error saving job: {e}")
        return False


def get_all_jobs():
    """Get all jobs from DynamoDB"""
    try:
        response = jobs_table.scan()
        items = response.get('Items', [])

        if items:
            df_data = {
                'Name': [item.get('fileName', '') for item in items],
                'Context': [item.get('rawText', '') for item in items],
                'Cleaned': [item.get('cleanedText', '') for item in items],
                'Description': [item.get('description', '') for item in items],
                'ID': [item.get('jobId', '') for item in items]
            }
            return pd.DataFrame(df_data)
        return pd.DataFrame(columns=['Name', 'Context', 'Cleaned', 'Description', 'ID'])
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
        return pd.DataFrame(columns=['Name', 'Context', 'Cleaned', 'Description', 'ID'])


def save_match_result(match_id, resume_id, job_id, score, details):
    """Save match result to DynamoDB"""
    try:
        item = {
            'matchId': match_id,
            'score': str(score * 100),
            'resumeId': resume_id,
            'jobId': job_id,
            'details': str(details),
            'matchedAt': datetime.now().isoformat()
        }
        matches_table.put_item(Item=item)
        return True
    except Exception as e:
        st.error(f"Error saving match: {e}")
        return False


def calculate_similarity(text1, text2):
    """Calculate similarity between two texts using spaCy"""
    try:
        # doc1 = nlp(str(text1))
        # doc2 = nlp(str(text2))
        return Similar.match(str(text1), str(text1))
    except Exception as e:
        st.error(f"Error calculating similarity: {e}")
        return 0.0


# ========================= Text Processing Functions =========================
def clean_text(text):
    """Clean and process text using spaCy"""
    import Cleaner
    return Cleaner.Cleaner(text)


# ========================= Streamlit Page Configuration =========================
st.set_page_config(
    page_title="Resume Matcher - Bulk Job Comparison",
    page_icon="📄",
    layout="wide"
)


# ========================= Styling =========================
def get_base64(bin_file):
    """Convert image to base64 - with fallback for missing files"""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""


# Try to load background image
bin_str = None #get_base64("Images/bg.jpg")
if bin_str:
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Try to load logo
try:
    image = Image.open('Images/logo.png')
    st.image(image, use_container_width=True)
except FileNotFoundError:
    st.markdown("# 📄 Resume Matcher")

# Title styling
new_title = '''
<style>
.title {
    font-size: 50px;
    font-weight: bold;
    color: #2a6592;
    text-align: center;
    padding: 20px;
}
</style>
<p class="title">Resume vs Job Descriptions Comparison</p>
'''
st.markdown(new_title, unsafe_allow_html=True)

# Additional styling
style = """
<style>
.stSlider > div > div > div {
    background-color: #2a6592;
}
.stButton > button {
    background-color: #2a6592;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    padding: 10px 20px;
}
.stButton > button:hover {
    background-color: #1e4a6b;
}
.match-high {
    background-color: #d4edda;
    padding: 10px;
    border-radius: 5px;
    border-left: 5px solid #28a745;
}
.match-medium {
    background-color: #fff3cd;
    padding: 10px;
    border-radius: 5px;
    border-left: 5px solid #ffc107;
}
.match-low {
    background-color: #f8d7da;
    padding: 10px;
    border-radius: 5px;
    border-left: 5px solid #dc3545;
}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

# Divider
st.markdown('<hr style="border: 2px solid #2a6592;">', unsafe_allow_html=True)

# ========================= Session State Initialization =========================
if 'uploaded_resume' not in st.session_state:
    st.session_state.uploaded_resume = None
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = None
if 'resume_processed' not in st.session_state:
    st.session_state.resume_processed = False
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

# ========================= Main Application =========================

# Sidebar for file uploads
with st.sidebar:
    st.header("📤 Upload Files")

    # Tab selection
    upload_tab = st.radio("Upload Mode", ["Single Resume", "Bulk Job Descriptions", "Process S3 Jobs"])

    st.markdown("---")

    if upload_tab == "Single Resume":
        # Resume Upload
        st.subheader("Upload Resume")
        uploaded_resume = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx', 'doc'],
            help="Upload resume in PDF or DOCX format"
        )

        if uploaded_resume is not None:
            if st.button("Process Resume", key="process_resume"):
                with st.spinner("Uploading and processing resume..."):
                    file_key = f"resumes/{uuid.uuid4()}_{uploaded_resume.name}"
                    s3_path = upload_file_to_s3(uploaded_resume, S3_BUCKET_RESUMES, file_key)

                    if s3_path:
                        st.success("✅ Resume uploaded to S3!")

                        extracted_text = extract_text_from_s3_file(S3_BUCKET_RESUMES, file_key)

                        if extracted_text:
                            cleaned_text = clean_text(extracted_text)
                            info = extractor(extracted_text)

                            resume_data = {
                                'name': uploaded_resume.name,
                                'raw_text': extracted_text,
                                'cleaned_text': cleaned_text,
                                'email': ', '.join(info.get('emails', [])) if info.get('emails') else '',
                                'phone': ', '.join(info.get('phone_numbers', [])) if info.get('phone_numbers') else '',
                                's3_key': file_key
                            }

                            resume_id = file_key.split('/')[-1]
                            if save_resume_to_dynamodb(resume_id, resume_data):
                                st.success("✅ Resume processed and stored!")
                                st.session_state.uploaded_resume = resume_data
                                st.session_state.resume_text = extracted_text
                                st.session_state.resume_processed = True
                            else:
                                st.error("❌ Failed to save resume data")

    elif upload_tab == "Bulk Job Descriptions":
        st.subheader("Bulk Upload Job Descriptions")
        uploaded_jobs = st.file_uploader(
            "Choose job description files",
            type=['pdf', 'docx', 'doc', 'txt'],
            accept_multiple_files=True,
            help="Upload multiple job descriptions at once"
        )

        if uploaded_jobs:
            st.info(f"📁 {len(uploaded_jobs)} files selected")

            if st.button("Upload All to S3", key="bulk_upload"):
                with st.spinner("Uploading files to S3..."):
                    uploaded_count, failed_files = bulk_upload_to_s3(
                        uploaded_jobs,
                        S3_BUCKET_JOBS,
                        prefix='jobs/'
                    )

                    if uploaded_count > 0:
                        st.success(f"✅ Successfully uploaded {uploaded_count} files to S3!")

                    if failed_files:
                        st.error(f"❌ Failed to upload: {', '.join(failed_files)}")

                    st.info("💡 Use 'Process S3 Jobs' tab to process these files")

    else:  # Process S3 Jobs
        st.subheader("Process Jobs from S3")
        st.info("This will process all unprocessed job files from S3")

        if st.button("Process All S3 Jobs", key="process_s3"):
            with st.spinner("Processing job descriptions from S3..."):
                processed_count = process_bulk_jobs_from_s3(S3_BUCKET_JOBS, prefix='jobs/')

                if processed_count > 0:
                    st.success(f"✅ Processed {processed_count} job descriptions!")
                    st.balloons()
                else:
                    st.info("ℹ️ No new jobs to process")

# ========================= Main Content Area =========================

# Load jobs from DynamoDB
Jobs = get_all_jobs()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Job Descriptions Library", "🔍 Compare Resume", "📈 Match Results"])

# Tab 1: Job Descriptions Library
with tab1:
    st.markdown("### 📚 Available Job Descriptions")

    if len(Jobs) == 0:
        st.warning("⚠️ No job descriptions found. Please upload job descriptions using the sidebar.")
    else:
        st.success(f"✅ Total Job Descriptions: **{len(Jobs)}**")

        # Display jobs in a nice table with selection
        st.markdown("#### Select Job Descriptions to View")

        # Create display dataframe
        display_df = pd.DataFrame({
            'Select': [False] * len(Jobs),
            'Job Title': Jobs['Name'],
            'Preview': Jobs['Description'].apply(lambda x: x[:100] + '...' if len(str(x)) > 100 else x),
            'ID': Jobs['ID']
        })

        # Interactive dataframe with selection
        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select jobs to view details",
                    default=False,
                )
            },
            disabled=["Job Title", "Preview", "ID"],
            hide_index=True,
            use_container_width=True
        )

        # Show selected job details
        selected_jobs = edited_df[edited_df['Select'] == True]

        if len(selected_jobs) > 0:
            st.markdown(f"#### 📋 Selected Jobs: {len(selected_jobs)}")

            for idx, row in selected_jobs.iterrows():
                with st.expander(f"📄 {row['Job Title']}"):
                    job_context = Jobs.loc[Jobs['ID'] == row['ID'], 'Context'].values[0]
                    st.text_area(
                        "Full Description",
                        value=job_context,
                        height=300,
                        key=f"job_desc_{idx}"
                    )

# Tab 2: Compare Resume
with tab2:
    st.markdown("### 🔍 Resume Comparison")

    if not st.session_state.resume_processed or st.session_state.uploaded_resume is None:
        st.info("👆 Please upload a resume using the sidebar to start comparison")
    elif len(Jobs) == 0:
        st.warning("⚠️ No job descriptions available. Please upload job descriptions first.")
    else:
        resume_data = st.session_state.uploaded_resume

        # Display resume info
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📧 Resume Information")
            st.write(f"**File:** {resume_data.get('name', 'Unknown')}")
            st.write(f"**Email:** {resume_data.get('email', 'Not found')}")
            st.write(f"**Phone:** {resume_data.get('phone', 'Not found')}")

        with col2:
            st.markdown("#### 📊 Comparison Options")
            comparison_mode = st.radio(
                "Select Comparison Mode",
                ["Compare with Selected Jobs", "Compare with All Jobs"]
            )

        st.markdown("---")

        if comparison_mode == "Compare with Selected Jobs":
            st.markdown("#### Select Jobs to Compare")

            # Multi-select for jobs
            selected_job_names = st.multiselect(
                "Choose job descriptions",
                options=Jobs['Name'].tolist(),
                default=Jobs['Name'].tolist()[:min(5, len(Jobs))]
            )

            if st.button("🚀 Compare with Selected Jobs", key="compare_selected"):
                if not selected_job_names:
                    st.warning("Please select at least one job description")
                else:
                    with st.spinner("Calculating match scores..."):
                        results = []
                        resume_text = resume_data.get('cleaned_text', '')

                        progress_bar = st.progress(0)

                        for idx, job_name in enumerate(selected_job_names):
                            job_row = Jobs[Jobs['Name'] == job_name].iloc[0]
                            job_text = job_row['Cleaned']

                            # Calculate similarity
                            score = calculate_similarity(resume_text, job_text)

                            results.append({
                                'Job Title': job_name,
                                'Match Score': score * 100,
                                'Score': score,
                                'Job ID': job_row['ID']
                            })

                            # Save match result
                            match_id = f"{resume_data.get('name', '')}_{job_name}_{uuid.uuid4()}"
                            save_match_result(
                                match_id,
                                resume_data.get('name', ''),
                                job_name,
                                score,
                                f"Match score: {score * 100:.2f}%"
                            )

                            progress = (idx + 1) / len(selected_job_names)
                            progress_bar.progress(progress)

                        progress_bar.empty()

                        # Sort by score
                        results_df = pd.DataFrame(results)
                        results_df = results_df.sort_values('Match Score', ascending=False)

                        st.session_state.comparison_results = results_df
                        st.success("✅ Comparison complete!")

        else:  # Compare with All Jobs
            if st.button("🚀 Compare with All Jobs", key="compare_all"):
                with st.spinner("Calculating match scores for all jobs..."):
                    results = []
                    resume_text = resume_data.get('cleaned_text', '')

                    progress_bar = st.progress(0)

                    for idx, row in Jobs.iterrows():
                        job_text = row['Cleaned']
                        score = calculate_similarity(resume_text, job_text)

                        results.append({
                            'Job Title': row['Name'],
                            'Match Score': score * 100,
                            'Score': score,
                            'Job ID': row['ID']
                        })

                        # Save match result
                        match_id = f"{resume_data.get('name', '')}_{row['Name']}_{uuid.uuid4()}"
                        save_match_result(
                            match_id,
                            resume_data.get('name', ''),
                            row['Name'],
                            score,
                            f"Match score: {score * 100:.2f}%"
                        )

                        progress = (idx + 1) / len(Jobs)
                        progress_bar.progress(progress)

                    progress_bar.empty()

                    # Sort by score
                    results_df = pd.DataFrame(results)
                    results_df = results_df.sort_values('Match Score', ascending=False)

                    st.session_state.comparison_results = results_df
                    st.success("✅ Comparison complete!")

# Tab 3: Match Results
with tab3:
    st.markdown("### 📈 Match Results & Rankings")

    if st.session_state.comparison_results is None:
        st.info("No comparison results yet. Use the 'Compare Resume' tab to generate results.")
    else:
        results_df = st.session_state.comparison_results

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jobs Compared", len(results_df))
        with col2:
            best_match = results_df.iloc[0]['Match Score']
            st.metric("Best Match", f"{best_match:.2f}%")
        with col3:
            avg_match = results_df['Match Score'].mean()
            st.metric("Average Match", f"{avg_match:.2f}%")
        with col4:
            high_matches = len(results_df[results_df['Match Score'] >= 70])
            st.metric("High Matches (≥70%)", high_matches)

        st.markdown("---")

        # Display ranked results
        st.markdown("#### 🏆 Ranked Job Matches")

        # Add rank column
        results_df_display = results_df.copy()
        results_df_display.insert(0, 'Rank', range(1, len(results_df_display) + 1))

        # Format the display
        results_df_display['Match Score'] = results_df_display['Match Score'].apply(lambda x: f"{x:.2f}%")


        # Color code based on score
        def highlight_rows(row):
            score = float(row['Match Score'].rstrip('%'))
            if score >= 75:
                return ['background-color: #d4edda'] * len(row)
            elif score >= 50:
                return ['background-color: #fff3cd'] * len(row)
            else:
                return ['background-color: #f8d7da'] * len(row)


        # Display styled dataframe
        st.dataframe(
            results_df_display[['Rank', 'Job Title', 'Match Score']],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # Detailed view for top matches
        st.markdown("#### 📊 Top 5 Matches - Detailed View")

        top_5 = results_df.head(5)

        for idx, row in top_5.iterrows():
            score = row['Match Score']

            if score >= 75:
                match_class = "match-high"
                emoji = "🟢"
            elif score >= 50:
                match_class = "match-medium"
                emoji = "🟡"
            else:
                match_class = "match-low"
                emoji = "🔴"

            with st.expander(f"{emoji} {row['Job Title']} - {score:.2f}%"):
                col1, col2 = st.columns([1, 2])

                with col1:
                    # Gauge chart for individual score
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Match Score"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 75], 'color': "yellow"},
                                {'range': [75, 100], 'color': "lightgreen"}
                            ]
                        }
                    ))
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Get job description
                    job_desc = Jobs[Jobs['ID'] == row['Job ID']]['Context'].values[0]
                    st.text_area(
                        "Job Description Preview",
                        value=job_desc[:500] + "..." if len(job_desc) > 500 else job_desc,
                        height=200,
                        key=f"preview_{idx}"
                    )

        # Download results
        st.markdown("---")
        st.markdown("#### 💾 Export Results")

        csv = results_df_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"resume_match_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # Visualization
        st.markdown("---")
        st.markdown("#### 📊 Score Distribution")

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=results_df['Job Title'],
            y=results_df['Match Score'],
            marker=dict(
                color=results_df['Match Score'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Score %")
            ),
            text=results_df['Match Score'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))

        fig.update_layout(
            title="Match Scores for All Jobs",
            xaxis_title="Job Title",
            yaxis_title="Match Score (%)",
            height=500,
            xaxis={'tickangle': -45}
        )

        st.plotly_chart(fig, use_container_width=True)

# ========================= Footer =========================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Resume Matcher - Bulk Comparison Tool</strong></p>
    <p>Powered by AWS: S3 | DynamoDB | ECS | Lambda</p>
    <p>NLP Engine: spaCy</p>
</div>
""", unsafe_allow_html=True)
