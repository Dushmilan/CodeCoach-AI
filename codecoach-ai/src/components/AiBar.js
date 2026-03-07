import React from 'react';
import './AiBar.css';

const AiBar = () => {
  return (
    <div className="ai-bar">
      <h2>AI Assistant</h2>
      <div className="ai-content">
        <p>I am here to help you with your code. Ask me anything or I'll provide suggestions as you type.</p>
        <div className="ai-chat">
          <input type="text" placeholder="Ask AI..." className="ai-input" />
        </div>
      </div>
    </div>
  );
};

export default AiBar;
