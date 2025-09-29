// src/pages/DataTablePage.jsx
import React, { useEffect, useState } from 'react';
import useApi from '../hooks/useApi';

const DataTablePage = () => {
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const { get } = useApi();

  useEffect(() => {
    const fetchTableData = async () => {
      const result = await get('/data');
      setLoading(false);
      
      if (!result.error && result.data && result.data.length > 0) {
        setTableData(result.data);
        setColumns(Object.keys(result.data[0]));
      }
    };

    fetchTableData();
  }, [get]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading data...</div>
      </div>
    );
  }

  if (tableData.length === 0) {
    return (
      <div className="page-container">
        <div className="no-data-state">
          <h2>Data Table</h2>
          <p>No data uploaded yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Data Table</h1>
        <p>Showing {tableData.length} rows</p>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column}>{row[column]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTablePage;