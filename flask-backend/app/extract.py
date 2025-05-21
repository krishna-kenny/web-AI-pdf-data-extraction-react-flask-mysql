import boto3
import time
import os
import sys
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

def print_tables(tables, document_key):
    if not tables:
        print(f"[WARN] No tables found in document: {document_key}")
        return

    print(f"[INFO] Extracted {len(tables)} table(s) from document: {document_key}\n")
    for idx, table in enumerate(tables):
        print(f"--- Table {idx + 1} ---")
        for row in table:
            print(row)
        print("\n")

def delete_file_from_s3(bucket, key):
    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"[INFO] Deleted file from S3: {key}")
    except Exception as e:
        print(f"[ERROR] Failed to delete {key} from S3: {e}")

def process_document(bucket, key):
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
        print_tables(tables, key)
        # Delete file after successful extraction
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

        for pdf_key in pdf_files:
            process_document(S3_BUCKET, pdf_key)

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <user_id>")
    else:
        main(sys.argv[1])
