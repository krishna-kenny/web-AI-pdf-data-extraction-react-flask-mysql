import { useState, useEffect } from "react";
import EditableTables from "./EditableTable";
import "./css/Finalize.css";

function Finalize({ userId, onClose }) {
  const [tables, setTables] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");

  useEffect(() => {
    async function fetchTables() {
      try {
        const res = await fetch(`/api/invoices/finalize?user_id=${userId}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to fetch tables");
        setTables(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (userId) fetchTables();
  }, [userId]);

  const handleFinalize = async () => {
    setSaving(true);
    setSaveStatus("Saving...");

    try {
      const res = await fetch("/api/invoices/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, tables }),
      });

      const data = await res.json();

      if (res.ok) {
        setSaveStatus("✅ Finalization successful!");
        setTimeout(() => {
          setSaveStatus("");
          onClose();
        }, 1500);
      } else {
        setSaveStatus(`❌ ${data.error || "Failed to save data"}`);
      }
    } catch (err) {
      setSaveStatus(`❌ Network error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="finalize-overlay">
        <div className="finalize-content">Loading final data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="finalize-overlay">
        <div className="finalize-content">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="finalize-overlay" onClick={onClose}>
      <div className="finalize-content" onClick={(e) => e.stopPropagation()}>
        <button
          className="finalize-close-btn"
          onClick={onClose}
          aria-label="Close"
        >
          &times;
        </button>

        <h2>Finalize Data</h2>

        <EditableTables tables={tables} setTables={setTables} />

        {saveStatus && <p className="finalize-status">{saveStatus}</p>}

        <button
          className="finalize-btn"
          onClick={handleFinalize}
          disabled={saving}
        >
          {saving ? "Saving..." : "Finalize"}
        </button>
      </div>
    </div>
  );
}

export default Finalize;
