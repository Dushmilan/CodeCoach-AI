import React, { useState } from 'react';
import './ApiKeyModal.css';

const ApiKeyModal = ({ onSave }) => {
  const [key, setKey] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (key.trim()) {
      onSave(key.trim());
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Enter NVIDIA NIM API Key</h2>
        <p>To use the AI Assistant, please provide your NVIDIA API key. This key will be stored in <strong>memory only</strong> and will not be saved to your device.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="nvapi-..."
            value={key}
            onChange={(e) => setKey(e.target.value)}
            required
            autoFocus
          />
          <div className="modal-info">
            Get your free key at <a href="https://build.nvidia.com/meta/llama-3.1-8b-instruct" target="_blank" rel="noopener noreferrer">build.nvidia.com</a>
          </div>
          <button type="submit" className="save-btn">Start Coding</button>
        </form>
      </div>
    </div>
  );
};

export default ApiKeyModal;
