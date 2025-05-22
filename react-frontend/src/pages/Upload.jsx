import { useState, useRef } from "react";
import Finalize from "./Finalize";
import "./css/Upload.css";

function Upload() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]); // Track uploaded filenames
  const [extractStatus, setExtractStatus] = useState("");
  const [showFinalize, setShowFinalize] = useState(false);
  const fileInputRef = useRef(null);

  // Get the logged-in user from localStorage
  const userId = localStorage.getItem("user_id");

  const validateFiles = (fileList) => {
    const allowedTypes = ["application/pdf"];
    const maxSize = 10 * 1024 * 1024; // 10 MB

    for (const file of fileList) {
      if (!allowedTypes.includes(file.type)) {
        setStatus(`❌ ${file.name} is not a PDF.`);
        return false;
      }
      if (file.size > maxSize) {
        setStatus(`❌ ${file.name} exceeds ${maxSize / (1024 * 1024)} MB.`);
        return false;
      }
    }
    return true;
  };

  const handleChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (validateFiles(selectedFiles)) {
      setFiles(selectedFiles);
      setStatus("");
      setUploadedFiles([]); // Reset uploaded files on new selection
      setExtractStatus("");
      setShowFinalize(false); // Reset finalize overlay on new selection
    } else {
      setFiles([]);
      setUploadedFiles([]);
      setExtractStatus("");
      setShowFinalize(false);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("user_id", userId); // Add user_id to form data

    try {
      const res = await fetch("/api/invoices/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setStatus(`✅ Uploaded ${data.filenames.length} file(s) successfully.`);
        setUploadedFiles(data.filenames);
        setFiles([]);
        if (fileInputRef.current) {
          fileInputRef.current.value = null;
        }
      } else {
        const errorMessage = data?.error || "Something went wrong.";
        setStatus(`❌ ${errorMessage}`);
        setUploadedFiles([]);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      setStatus("❌ Network error. Try again.");
      setUploadedFiles([]);
    }
  };

  const handleExtract = async () => {
    if (uploadedFiles.length === 0) {
      setExtractStatus("❌ No files uploaded to extract.");
      return;
    }
    setExtractStatus("⏳ Extraction in progress...");

    try {
      const user_id = localStorage.getItem("user_id") || "";

      const res = await fetch("/api/invoices/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filenames: uploadedFiles, user_id }),
      });

      const data = await res.json();

      if (res.ok) {
        setExtractStatus(`✅ Extraction completed successfully.`);
        setShowFinalize(true); // Show Finalize overlay after success
        console.log("Extraction output:", data);
      } else {
        const errorMessage = data?.error || "Extraction failed.";
        setExtractStatus(`❌ ${errorMessage}`);
      }
    } catch (error) {
      console.error("Extraction failed:", error);
      setExtractStatus("❌ Network error during extraction.");
    }
  };

  return (
    <div className="page">
      <div className="container">
        <h1 className="title">Upload PDF Invoices</h1>

        <input
          type="file"
          accept="application/pdf"
          multiple
          onChange={handleChange}
          id="file-upload"
          className="file-input"
          ref={fileInputRef}
        />
        <label htmlFor="file-upload" className="btn">
          Select PDF files
        </label>

        {files.length > 0 && (
          <>
            <h2 className="secondary-title">Selected PDF file(s)</h2>
            <ul className="file-list">
              {files.map((file, i) => (
                <li key={`${file.name}-${i}`} className="file-item">
                  <span className="file-icon">📄</span>
                  <span>{file.name}</span>
                </li>
              ))}
            </ul>

            <button onClick={handleUpload} className="btn upload-btn">
              Upload
            </button>
          </>
        )}

        {status && <p className="status">{status}</p>}

        {/* Show Extract button only after successful upload */}
        {uploadedFiles.length > 0 && (
          <>
            <button
              onClick={handleExtract}
              className="btn extract-btn"
              style={{ marginTop: "1rem" }}
            >
              Begin Extraction
            </button>
            {extractStatus && <p className="status">{extractStatus}</p>}
          </>
        )}
      </div>

      {showFinalize && (
        <Finalize userId={userId} onClose={() => setShowFinalize(false)} />
      )}
    </div>
  );
}

export default Upload;
