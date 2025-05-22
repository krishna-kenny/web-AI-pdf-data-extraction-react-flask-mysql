import React, { useState } from "react";

function EditableTables({ tables, setTables }) {
  const [editingCell, setEditingCell] = useState(null);
  // editingCell = { filename, rowIndex, cellIndex } or null

  if (!tables || Object.keys(tables).length === 0)
    return <div>No tables to display</div>;

  // Update the value for a specific cell
  const handleCellChange = (filename, rowIndex, cellIndex, newValue) => {
    setTables((prevTables) => {
      const newTables = { ...prevTables };
      const newTable = newTables[filename].map((row) => [...row]);
      newTable[rowIndex][cellIndex] = newValue;
      newTables[filename] = newTable;
      return newTables;
    });
  };

  // When input loses focus or enter is pressed, stop editing
  const handleFinishEditing = () => {
    setEditingCell(null);
  };

  return (
    <div>
      {Object.entries(tables).map(([filename, table]) => (
        <div key={filename} style={{ marginBottom: "2rem" }}>
          <h3>{filename.split("/").pop()}</h3>
          <table border="1" cellPadding="5" cellSpacing="0" style={{ borderCollapse: "collapse", width: "100%" }}>
            <tbody>
              {table.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => {
                    const isEditing =
                      editingCell &&
                      editingCell.filename === filename &&
                      editingCell.rowIndex === rIdx &&
                      editingCell.cellIndex === cIdx;

                    return (
                      <td
                        key={cIdx}
                        onClick={() => setEditingCell({ filename, rowIndex: rIdx, cellIndex: cIdx })}
                        style={{ cursor: "pointer", padding: "6px" }}
                      >
                        {isEditing ? (
                          <input
                            autoFocus
                            type="text"
                            value={cell}
                            onChange={(e) => handleCellChange(filename, rIdx, cIdx, e.target.value)}
                            onBlur={handleFinishEditing}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleFinishEditing();
                              } else if (e.key === "Escape") {
                                // Cancel editing without saving (optional)
                                setEditingCell(null);
                              }
                            }}
                            style={{ width: "100%", boxSizing: "border-box" }}
                          />
                        ) : (
                          cell
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

export default EditableTables;
