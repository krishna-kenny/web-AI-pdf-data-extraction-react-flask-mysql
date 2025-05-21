# upload.py
from flask import request, jsonify
from werkzeug.utils import secure_filename
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "cargofl-ai-invoice-reader-test")
S3_UPLOAD_PREFIX = "uploads"
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_files_to_s3(files, user_id):
    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    uploaded = []
    errors = []

    for file in files:
        original_name = file.filename or ""
        if not allowed_file(original_name):
            errors.append(f"Invalid file type: {original_name}")
            continue

        filename = secure_filename(original_name)
        # Prefix with user_id and upload prefix to isolate files per user
        key = f"{S3_UPLOAD_PREFIX}/{user_id}/{filename}"

        try:
            s3.upload_fileobj(
                Fileobj=file.stream,
                Bucket=S3_BUCKET,
                Key=key,
                ExtraArgs={
                    'ContentType': file.mimetype,
                    'ACL': 'private'  # Keep files private
                }
            )
            uploaded.append(key)
        except Exception as e:
            print(f"[ERROR] S3 upload failed for {filename}: {e}")
            errors.append(f"Failed to upload {filename}: {str(e)}")

    return uploaded, errors


def delete_files_from_s3(keys):
    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    for key in keys:
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=key)
            print(f"Deleted file from S3: {key}")
        except Exception as e:
            print(f"[ERROR] Failed to delete {key}: {e}")
