// src/components/Topbar.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload } from 'lucide-react';

const Topbar = () => {
  const navigate = useNavigate();

  return (
    <div className="topbar">
      <div className="topbar-left">
        <h1 className="app-title">DataViz App</h1>
      </div>
      <div className="topbar-right">
        <button 
          className="upload-button"
          onClick={() => navigate('/upload')}
        >
          <Upload size={18} />
          Upload Data
        </button>
      </div>
    </div>
  );
};

export default Topbar;