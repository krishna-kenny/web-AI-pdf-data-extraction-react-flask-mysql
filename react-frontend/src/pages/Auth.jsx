import React, { useState } from "react";
import "./css/Auth.css";

export default function Auth({ onAuthSuccess }) {
  const [user_id, setuser_id] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (user_id === password) {
      localStorage.setItem("user_id", user_id); // Store logged-in user
      setError("");
      onAuthSuccess();
    } else {
      setError("Incorrect user_id or password");
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="user_id"
            value={user_id}
            onChange={(e) => setuser_id(e.target.value)}
            required
            autoFocus
            className="auth-input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="auth-input"
          />
          <button type="submit" className="auth-btn">
            Login
          </button>
        </form>
        {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}
      </div>
    </div>
  );
}
