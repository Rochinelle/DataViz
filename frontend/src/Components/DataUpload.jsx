// src/components/DataUpload.jsx
import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import useApi from '../hooks/useApi';

const DataUpload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const fileInputRef = useRef(null);
  const { post, loading } = useApi();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'text/csv' || droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setMessage('');
      } else {
        setMessage('Please upload a CSV file only.');
        setMessageType('error');
      }
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'text/csv' || selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setMessage('');
      } else {
        setMessage('Please upload a CSV file only.');
        setMessageType('error');
      }
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setMessage('Please select a file first.');
      setMessageType('error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const result = await post('/api/data/upload', formData);
    
    if (result.error) {
      setMessage('Upload disabled - backend not available');
      setMessageType('error');
    } else {
      setMessage('File uploaded successfully!');
      setMessageType('success');
      setFile(null);
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2 className="upload-title">Upload Your Data</h2>
        
        <div 
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <Upload size={48} className="upload-icon" />
          <p className="upload-text">
            Drag and drop your CSV file here, or click to browse
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {file && (
          <div className="file-info">
            <FileText size={16} />
            <span>{file.name}</span>
          </div>
        )}

        <button 
          className={`upload-submit ${loading ? 'loading' : ''}`}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Uploading...' : 'Upload File'}
        </button>

        {message && (
          <div className={`message ${messageType}`}>
            {messageType === 'success' ? (
              <CheckCircle size={16} />
            ) : (
              <AlertCircle size={16} />
            )}
            <span>{message}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataUpload;