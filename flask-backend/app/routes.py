from flask import Blueprint, request, jsonify
from flask_cors import CORS
from app.upload import upload_files_to_s3
from app import extract
import subprocess
import sys
import os
import json

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})


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

        # Pass user_id to your upload function to prefix files
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
        username = data.get("username")

        if not username:
            return jsonify({"error": "Username not provided"}), 400

        args = [username]

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
