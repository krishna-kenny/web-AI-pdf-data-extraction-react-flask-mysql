import { useState } from "react";
import "./css/Search.css";

function Search() {
  const [query, setQuery] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortBy, setSortBy] = useState("date_desc");

  const handleSearch = () => {
    console.log({ query, startDate, endDate, sortBy });
  };

  return (
    <div className="search-page">
      <div className="filter-bar">

        <div className="filter-item search-item">
          <label htmlFor="search-input" className="filter-label">Search</label>
          <input
            id="search-input"
            type="text"
            className="search-input"
            placeholder="Invoice #, filename, client"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="start-date" className="filter-label">Start Date</label>
          <input
            id="start-date"
            type="date"
            className="date-input"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="end-date" className="filter-label">End Date</label>
          <input
            id="end-date"
            type="date"
            className="date-input"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="sort-select" className="filter-label">Sort By</label>
          <select
            id="sort-select"
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="date_desc">Date (Newest First)</option>
            <option value="date_asc">Date (Oldest First)</option>
            <option value="amount_desc">Amount (High to Low)</option>
            <option value="amount_asc">Amount (Low to High)</option>
            <option value="filename_asc">Filename (A to Z)</option>
            <option value="filename_desc">Filename (Z to A)</option>
          </select>
        </div>

        <div className="filter-item">
          <button className="search-button" onClick={handleSearch}>Search</button>
        </div>

      </div>

      <main className="results-area">
        <h2>Results</h2>
        <p>No results yet. Perform a search to see invoices.</p>
      </main>
    </div>
  );
}

export default Search;
