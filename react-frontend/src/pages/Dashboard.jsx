import { useState } from "react";
import Upload from "./Upload";
import Search from "./Search";
import Manage from "./Manage";
import "./css/Dashboard.css";

function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState("upload");
  const [menuOpen, setMenuOpen] = useState(false);

  const renderTab = () => {
    switch (activeTab) {
      case "upload":
        return <Upload />;
      case "search":
        return <Search />;
      case "manage":
        return <Manage />;
      default:
        return null;
    }
  };

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    setMenuOpen(false);
  };

  return (
    <div className="dashboard">
      <header className="navbar">
        <div className="nav-logo">INVOICE</div>
        <button
          className="nav-toggle"
          aria-label="Toggle navigation menu"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span className="hamburger"></span>
          <span className="hamburger"></span>
          <span className="hamburger"></span>
        </button>
        <nav className={`nav-links ${menuOpen ? "open" : ""}`}>
          <span
            onClick={() => handleNavClick("upload")}
            className={activeTab === "upload" ? "active" : ""}
          >
            Upload
          </span>
          <span
            onClick={() => handleNavClick("search")}
            className={activeTab === "search" ? "active" : ""}
          >
            Search
          </span>
          <span
            onClick={() => handleNavClick("manage")}
            className={activeTab === "manage" ? "active" : ""}
          >
            Manage
          </span>
          <span onClick={onLogout}>Logout</span>
        </nav>
      </header>
      <main className="tab-content">{renderTab()}</main>
    </div>
  );
}

export default Dashboard;
