// src/components/SuggestionsPanel.jsx
import React, { useState, useEffect } from 'react';
import { Send, Lightbulb } from 'lucide-react';
import useApi from '../hooks/useApi';

const SuggestionsPanel = () => {
  const [userInput, setUserInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [insights, setInsights] = useState([]);
  const { get, post } = useApi();

  useEffect(() => {
    const fetchSuggestions = async () => {
      const result = await get('/api/suggestions/suggestions');
      if (!result.error && result.data) {
        setSuggestions(result.data.suggestions || []);
      }
    };

    fetchSuggestions();
  }, [get]);

  const handleInsightRequest = async () => {
    if (!userInput.trim()) return;

    const result = await post('/insights', { query: userInput });
    if (!result.error && result.data) {
      setInsights(prev => [...prev, {
        query: userInput,
        response: result.data.insight || 'No insight available'
      }]);
      setUserInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleInsightRequest();
    }
  };

  return (
    <div className="suggestions-panel">
      <div className="suggestions-header">
        <h3>Insights & Suggestions</h3>
      </div>

      <div className="insights-input">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask for insights (e.g., 'average salary by department')"
          className="insight-input"
        />
        <button 
          onClick={handleInsightRequest}
          className="insight-submit"
          disabled={!userInput.trim()}
        >
          <Send size={16} />
        </button>
      </div>

      {insights.length > 0 && (
        <div className="insights-list">
          <h4>Your Insights:</h4>
          {insights.map((insight, index) => (
            <div key={index} className="insight-item">
              <p className="insight-query">{insight.query}</p>
              <p className="insight-response">{insight.response}</p>
            </div>
          ))}
        </div>
      )}

      <div className="suggestions-list">
        <h4>
          <Lightbulb size={16} />
          System Suggestions:
        </h4>
        {suggestions.length > 0 ? (
          suggestions.map((suggestion, index) => (
            <div key={index} className="suggestion-item">
              {suggestion}
            </div>
          ))
        ) : (
          <p className="no-data-text">Upload data to see insights</p>
        )}
      </div>
    </div>
  );
};

export default SuggestionsPanel;