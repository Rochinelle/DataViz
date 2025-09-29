// src/pages/VisualizationPage.jsx
import React, { useState, useEffect } from 'react';
import ChartRender from '../Components/ChartRender';
import useApi from '../hooks/useApi';

const VisualizationPage = () => {
  const [chartData, setChartData] = useState([]);
  const [chartType, setChartType] = useState('bar');
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [availableColumns, setAvailableColumns] = useState([]);
  const { get } = useApi();

  useEffect(() => {
    const fetchData = async () => {
      const result = await get('/data');
      if (!result.error && result.data && result.data.length > 0) {
        setChartData(result.data);
        const columns = Object.keys(result.data[0]);
        setAvailableColumns(columns);
        if (columns.length > 0) {
          setXAxis(columns[0]);
          setYAxis(columns[1] || columns[0]);
        }
      }
    };

    fetchData();
  }, [get]);

  if (chartData.length === 0) {
    return (
      <div className="page-container">
        <div className="no-data-state">
          <h2>Visualizations</h2>
          <p>No data uploaded yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Data Visualizations</h1>
      </div>

      <div className="chart-controls">
        <div className="control-group">
          <label>Chart Type:</label>
          <select 
            value={chartType} 
            onChange={(e) => setChartType(e.target.value)}
            className="control-select"
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
            <option value="pie">Pie Chart</option>
          </select>
        </div>

        <div className="control-group">
          <label>X-Axis:</label>
          <select 
            value={xAxis} 
            onChange={(e) => setXAxis(e.target.value)}
            className="control-select"
          >
            {availableColumns.map((column) => (
              <option key={column} value={column}>{column}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Y-Axis:</label>
          <select 
            value={yAxis} 
            onChange={(e) => setYAxis(e.target.value)}
            className="control-select"
          >
            {availableColumns.map((column) => (
              <option key={column} value={column}>{column}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="visualization-area">
        <ChartRender
          type={chartType}
          data={chartData.slice(0, 20)}
          xKey={xAxis}
          yKey={yAxis}
          height={500}
          title={`${chartType.toUpperCase()} Chart: ${yAxis} by ${xAxis}`}
        />
      </div>
    </div>
  );
};

export default VisualizationPage;