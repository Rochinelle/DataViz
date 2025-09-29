// src/components/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import { BarChart3, Database, PieChart } from 'lucide-react';
import StatCard from './StatCard';
import ChartRender from './ChartRender';
import SuggestionsPanel from './SuggestionsPanel';
import useApi from '../hooks/useApi';

const Dashboard = () => {
  const [stats, setStats] = useState({ rows: 0, columns: 0, charts: 0 });
  const [chartData, setChartData] = useState([]);
  const { get } = useApi();

  useEffect(() => {
    const fetchDashboardData = async () => {
      // Fetch summary stats
      const summaryResult = await axios.get('/summary', { params: { dataset: 1 } });
      if (!summaryResult.error && summaryResult.data) {
        setStats({
          rows: summaryResult.data.rows || 0,
          columns: summaryResult.data.columns || 0,
          charts: summaryResult.data.charts || 0,
        });
      }

      // Fetch chart data
      const dataResult = await axios.get('/data', { params: { dataset: 1 , limit: 100} });
      if (!dataResult.error && dataResult.data) {
        setChartData(dataResult.data.slice(0, 10)); // Limit to first 10 rows for visualization
      }
    };

    fetchDashboardData();
  }, [get]);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard Overview</h1>
      </div>

      <div className="stats-grid">
        <StatCard 
          icon={Database}
          title="Rows Processed"
          value={stats.rows}
        />
        <StatCard 
          icon={BarChart3}
          title="Columns Detected"
          value={stats.columns}
        />
        <StatCard 
          icon={PieChart}
          title="Charts Generated"
          value={stats.charts}
        />
      </div>

      <div className="dashboard-content">
        <div className="charts-section">
          <ChartRender
            type="bar"
            data={chartData}
            xKey="name"
            yKey="value"
            height={400}
            title="Data Visualization"
          />
        </div>

        <div className="insights-section">
          <SuggestionsPanel />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;