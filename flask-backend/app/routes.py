from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import boto3
import botocore
import os

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})  # Allow CORS from any origin

# ── CONFIGURATION CONSTANTS ─────────────────────────────────────────────

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN     = None
AWS_REGION            = "ap-south-1"

S3_BUCKET        = "cargofl-ai-invoice-reader-test"
S3_UPLOAD_PREFIX = "uploads"
# ────────────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/api/invoices/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files selected"}), 400

    # Initialize S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=AWS_REGION
    )

    uploaded = []
    errors = []

    for file in files:
        original_name = file.filename or ""
        if not allowed_file(original_name):
            errors.append(f"Invalid file type: {original_name}")
            continue

        filename = secure_filename(original_name)
        key = f"{S3_UPLOAD_PREFIX}/{filename}"

        try:
            s3.upload_fileobj(
                Fileobj=file.stream,
                Bucket=S3_BUCKET,
                Key=key,
                ExtraArgs={
                    'ContentType': file.mimetype,
                    'ACL': 'private'
                }
            )
            uploaded.append(key)
        except botocore.exceptions.ClientError as e:
            print(f"[ERROR] S3 upload failed for {filename}: {e}")
            errors.append(f"Failed to upload {filename}")

    # No uploads at all = total failure
    if not uploaded and errors:
        return jsonify({"error": errors}), 500

    # Partial or full success
    response = {
        "uploaded_keys": uploaded,
        "filenames": [key.split("/")[-1] for key in uploaded]
    }
    if errors:
        response["errors"] = errors

    return jsonify(response), 207 if errors else 200

