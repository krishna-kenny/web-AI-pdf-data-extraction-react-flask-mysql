import boto3
import time
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "cargofl-ai-invoice-reader-test")
S3_UPLOAD_PREFIX = "uploads"
POLL_INTERVAL = 5  # seconds

# Setup boto3 clients
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

textract = boto3.client(
    "textract",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def list_pdf_files(bucket, user_prefix):
    """List all PDF files under the user-specific prefix in the S3 bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    pdf_files = []

    for page in paginator.paginate(Bucket=bucket, Prefix=user_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".pdf"):
                pdf_files.append(key)

    return pdf_files

def start_table_detection(bucket, key):
    resp = textract.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES"]
    )
    return resp["JobId"]

def is_job_complete(job_id):
    resp = textract.get_document_analysis(JobId=job_id)
    return resp["JobStatus"], resp

def get_all_results(job_id):
    pages = []
    next_token = None
    while True:
        if next_token:
            resp = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
        else:
            resp = textract.get_document_analysis(JobId=job_id)
        pages.append(resp)
        next_token = resp.get("NextToken")
        if not next_token:
            break
    return pages

def extract_tables(pages):
    blocks = []
    for page in pages:
        blocks.extend(page["Blocks"])
    block_map = {b["Id"]: b for b in blocks}
    tables = [b for b in blocks if b["BlockType"] == "TABLE"]

    all_tables = []

    for table in tables:
        cells = []
        for rel in table.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for cid in rel["Ids"]:
                    cell = block_map[cid]
                    if cell["BlockType"] == "CELL":
                        cells.append(cell)

        max_row = max(cell["RowIndex"] for cell in cells) if cells else 0
        max_col = max(cell["ColumnIndex"] for cell in cells) if cells else 0
        grid = [["" for _ in range(max_col)] for _ in range(max_row)]

        for cell in cells:
            text = ""
            for rel in cell.get("Relationships", []):
                if rel["Type"] == "CHILD":
                    for tid in rel["Ids"]:
                        item = block_map[tid]
                        if item["BlockType"] == "WORD":
                            text += item["Text"] + " "
                        elif item["BlockType"] == "SELECTION_ELEMENT" and item["SelectionStatus"] == "SELECTED":
                            text += "X "
            grid[cell["RowIndex"] - 1][cell["ColumnIndex"] - 1] = text.strip()

        all_tables.append(grid)
    return all_tables

def save_table_to_json_and_upload(table, bucket, prefix, filename):
    """
    Save a 2D table list as JSON and upload to S3.
    """
    json_content = json.dumps(table)
    s3.put_object(
        Bucket=bucket,
        Key=f"{prefix}/{filename}",
        Body=json_content.encode('utf-8'),
        ContentType='application/json'
    )
    print(f"[INFO] Uploaded table as {prefix}/{filename} to S3.")

def delete_file_from_s3(bucket, key):
    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"[INFO] Deleted file from S3: {key}")
    except Exception as e:
        print(f"[ERROR] Failed to delete {key} from S3: {e}")

def process_document(bucket, key, doc_index):
    print(f"[INFO] Starting Textract TABLE analysis for {key}...")
    job_id = start_table_detection(bucket, key)
    print(f"[INFO] Job started. JobId: {job_id}")

    while True:
        status, resp = is_job_complete(job_id)
        print(f"[INFO] Job status for {key}: {status}")
        if status in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(POLL_INTERVAL)

    if status == "SUCCEEDED":
        pages = get_all_results(job_id)
        tables = extract_tables(pages)
        if not tables:
            print(f"[WARN] No tables found in document: {key}")
        else:
            # Get prefix/folder path for uploading JSONs, e.g. uploads/user_id/
            user_prefix = "/".join(key.split("/")[:-1])

            # Extract the base pdf filename without extension
            pdf_filename = os.path.splitext(os.path.basename(key))[0]

            for idx, table in enumerate(tables):
                # Compose filename as pdfname_1.json, pdfname_2.json, etc.
                filename = f"{pdf_filename}_{idx + 1}.json"
                save_table_to_json_and_upload(table, bucket, user_prefix, filename)

        # Delete original PDF after successful extraction
        delete_file_from_s3(bucket, key)
    else:
        print(f"[ERROR] Textract job failed for {key}: {resp}")

def main(user_id=None):
    if not user_id:
        print("[ERROR] User ID is required to scope files for extraction.")
        return

    user_prefix = f"{S3_UPLOAD_PREFIX}/{user_id}/"
    try:
        pdf_files = list_pdf_files(S3_BUCKET, user_prefix)
        if not pdf_files:
            print(f"[INFO] No PDF files found in S3 bucket for user {user_id}.")
            return

        for i, pdf_key in enumerate(pdf_files, 1):
            process_document(S3_BUCKET, pdf_key, i)

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <user_id>")
    else:
        main(sys.argv[1])
