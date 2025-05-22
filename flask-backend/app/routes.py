from flask import Blueprint, request, jsonify
from flask_cors import CORS
from app.upload import upload_files_to_s3
from app import finalize
import subprocess
import sys
import os
import json
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})

# Load AWS credentials and config from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')

# Initialize the S3 client with credentials and region
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)


@main.route('/api/invoices/upload', methods=['POST'])
def upload_files():
    try:
        user_id = request.form.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID missing"}), 400

        if 'files' not in request.files:
            return jsonify({"error": "No files part in the request"}), 400

        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files selected"}), 400

        uploaded, errors = upload_files_to_s3(files, user_id)

        if not uploaded and errors:
            return jsonify({"error": errors}), 500

        response = {
            "uploaded_keys": uploaded,
            "filenames": [key.split("/")[-1] for key in uploaded]
        }
        if errors:
            response["errors"] = errors

        return jsonify(response), 207 if errors else 200

    except Exception as e:
        print(f"[FATAL] Unexpected error during upload: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@main.route('/api/invoices/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(silent=True) or {}
        filenames = data.get("filenames")
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id not provided"}), 400

        args = [user_id]

        if filenames:
            args.append(json.dumps(filenames))

        extract_script = os.path.join(os.path.dirname(__file__), "extract.py")

        result = subprocess.run(
            [sys.executable, extract_script, *args],
            capture_output=True,
            text=True,
            check=True
        )

        print("[extract.py output]")
        print(result.stdout)

        return jsonify({"message": "Extraction started", "output": result.stdout}), 200

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Extract failed: {e.stderr}")
        return jsonify({"error": "Extraction failed", "details": e.stderr}), 500


@main.route('/api/invoices/finalize', methods=['GET'])
def finalize_route():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    try:
        # List objects in the user's folder (uploads/{user_id}/)
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"uploads/{user_id}/")
        files = response.get('Contents', [])

        tables = {}

        for obj in files:
            key = obj['Key']
            if key.endswith('.json'):
                filename = key.split('/')[-1].replace('.json', '')
                file_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
                content = file_obj['Body'].read().decode('utf-8')
                tables[filename] = json.loads(content)

        return jsonify(tables)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@main.route('/api/invoices/finalize', methods=['POST'])
def finalize_save():
    data = request.get_json()
    user_id = data.get('user_id')
    tables = data.get('tables')  # dict: filename -> list of rows (arrays)

    if not user_id or not tables:
        return jsonify({"error": "Missing user_id or tables"}), 400

    try:
        for filename, rows in tables.items():
            # Save JSON string of the table
            json_content = json.dumps(rows)

            s3.put_object(
                Bucket=S3_BUCKET,
                Key=f"uploads/{user_id}/{filename}.json",
                Body=json_content.encode('utf-8'),
                ContentType='application/json'
            )

        return jsonify({"message": "Tables finalized and saved as JSON."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
