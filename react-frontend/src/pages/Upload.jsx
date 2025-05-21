import { useState, useRef } from "react";
import "./css/Upload.css";

function Upload() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");
  const fileInputRef = useRef(null);

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
    } else {
      setFiles([]);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const res = await fetch("/api/invoices/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setStatus(`✅ Uploaded ${data.filenames.length} file(s) successfully.`);
        setFiles([]);
        if (fileInputRef.current) {
          fileInputRef.current.value = null;
        }
      } else {
        const errorMessage = data?.error || "Something went wrong.";
        setStatus(`❌ ${errorMessage}`);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      setStatus("❌ Network error. Try again.");
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
      </div>
    </div>
  );
}

export default Upload;
