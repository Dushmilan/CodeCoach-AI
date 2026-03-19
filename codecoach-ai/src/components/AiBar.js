import React, { useState, useRef, useEffect } from 'react';
import './AiBar.css';

const AiBar = ({ currentCode, selectedLanguage, question, apiKey }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "I am here to help you with your code. Ask me anything or I'll provide suggestions as you type." }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (!apiKey) {
        throw new Error('NVIDIA API Key is missing. Please enter it in the prompt.');
      }

      const systemPrompt = `You are an expert coding assistant for a platform called CodeCoach-AI.
Current context:
- Problem: ${question?.title || 'Unknown'}
- Language: ${selectedLanguage}
- Current Code: 
\`\`\`${selectedLanguage}
${currentCode}
\`\`\`

Provide helpful, concise, and accurate coding advice. If the user asks for a solution, guide them instead of just giving the full code.`;

      const response = await fetch('/api/nvidia/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: "meta/llama-3.1-8b-instruct",
          messages: [
            { role: 'system', content: systemPrompt },
            ...messages.slice(-5), // Keep last 5 messages for context
            userMessage
          ],
          max_tokens: 1024,
          temperature: 0.5,
          top_p: 1,
          stream: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch from NVIDIA NIM API');
      }

      const data = await response.json();
      const assistantMessage = {
        role: 'assistant',
        content: data.choices[0].message.content
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}. Make sure your API key is correct and you have enough credits.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ai-bar">
      <div className="ai-header">
        <h2>AI Assistant</h2>
        <span className="model-badge">Llama 3.1 8B</span>
      </div>
      
      <div className="ai-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant loading">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ai-chat-controls">
        <textarea 
          placeholder="Ask AI..." 
          className="ai-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={1}
        />
        <button 
          className="send-btn" 
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default AiBar;
