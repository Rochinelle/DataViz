// src/hooks/useApi.js
import { useState, useCallback } from 'react';
import axios from 'axios';

const useApi = () => {
  const [loading, setLoading] = useState(false);
  const baseURL = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

  const api = axios.create({
    baseURL,
    timeout: 10000,
  });

  const get = useCallback(async (endpoint, params = {}) => {
    setLoading(true);
    try {
      const response = await api.get(endpoint, { params });
      setLoading(false);
      return { data: response.data, error: false };
    } catch (error) {
      setLoading(false);
      console.error('API Error:', error);
      return { 
        data: null, 
        error: true, 
        message: error.response?.data?.message || 'Backend not available' 
      };
    }
  }, [api]);

  const post = useCallback(async (endpoint, data) => {
    setLoading(true);
    try {
      const response = await api.post(endpoint, data);
      setLoading(false);
      return { data: response.data, error: false };
    } catch (error) {
      setLoading(false);
      console.error('API Error:', error);
      return { 
        data: null, 
        error: true, 
        message: error.response?.data?.message || 'Backend not available' 
      };
    }
  }, [api]);

  return { get, post, loading };
};

export default useApi;