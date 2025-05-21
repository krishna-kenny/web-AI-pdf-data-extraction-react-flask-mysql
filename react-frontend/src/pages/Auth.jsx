import React, { useState } from "react";
import "./css/Auth.css";

export default function Auth({ onAuthSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username === "k" && password === "k") {
      localStorage.setItem("username", username); // Store logged-in user
      setError("");
      onAuthSuccess();
    } else {
      setError("Incorrect username or password");
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
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
