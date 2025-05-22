import boto3
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

# Setup boto3 client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def list_json_files(bucket, user_prefix):
    """List all JSON files under the user-specific prefix in the S3 bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    json_files = []

    for page in paginator.paginate(Bucket=bucket, Prefix=user_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".json"):
                json_files.append(key)

    return json_files

def download_json_as_list(bucket, key):
    """Download JSON from S3 and parse as list of rows (list of lists)."""
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_bytes = obj['Body'].read()
    json_str = json_bytes.decode('utf-8')
    data = json.loads(json_str)
    return data  # should be a list of lists

def get_user_json_tables(user_id):
    if not user_id:
        raise ValueError("User ID is required")

    user_prefix = f"{S3_UPLOAD_PREFIX}/{user_id}/"
    try:
        json_files = list_json_files(S3_BUCKET, user_prefix)
        if not json_files:
            return {}

        all_tables = {}
        for json_key in json_files:
            table_data = download_json_as_list(S3_BUCKET, json_key)
            all_tables[json_key] = table_data

        return all_tables

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")
        raise e

def main(user_id=None):
    if not user_id:
        print("[ERROR] User ID is required to scope files for finalization.")
        return

    user_prefix = f"{S3_UPLOAD_PREFIX}/{user_id}/"
    try:
        json_files = list_json_files(S3_BUCKET, user_prefix)
        if not json_files:
            print(f"[INFO] No JSON files found in S3 bucket for user {user_id}.")
            return

        all_tables = {}
        for json_key in json_files:
            table_data = download_json_as_list(S3_BUCKET, json_key)
            all_tables[json_key] = table_data
            print(f"[INFO] Loaded JSON {json_key} with {len(table_data)} rows.")

        # Now all_tables is a dict with key=filename, value=list-of-lists
        # You can process them here or return
        return all_tables

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python finalize.py <user_id>")
    else:
        tables = main(sys.argv[1])
        # For demo: print first 2 rows of each table
        if tables:
            for fname, table in tables.items():
                print(f"\nTable from file: {fname}")
                for row in table[:2]:
                    print(row)
