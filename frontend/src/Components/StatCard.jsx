// src/components/StatCard.jsx
import React from 'react';

const StatCard = ({ icon: Icon, title, value }) => {
  return (
    <div className="stat-card">
      <div className="stat-card-icon">
        <Icon size={24} />
      </div>
      <div className="stat-card-content">
        <h3 className="stat-card-title">{title}</h3>
        <p className="stat-card-value">{value || 0}</p>
      </div>
    </div>
  );
};

export default StatCard;