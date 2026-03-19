import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AiBar.css';

const AiBar = ({ currentCode, selectedLanguage, question, apiKey }) => {
  const initialMessage = { role: 'assistant', content: "I am your AI Coding Coach. I'm here to help you solve this problem through guidance and hints, not just by giving you the solution. What's on your mind?" };
  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (overrideInput = null) => {
    const messageText = overrideInput || input;
    if (!messageText.trim() || isLoading) return;

    const userMessage = { role: 'user', content: messageText };
    setMessages(prev => [...prev, userMessage]);
    if (!overrideInput) setInput('');
    setIsLoading(true);

    try {
      if (!apiKey) {
        throw new Error('NVIDIA API Key is missing. Please enter it in the prompt.');
      }

      const systemPrompt = `You are an expert coding coach for CodeCoach-AI. 
Your goal is to help users learn by providing guidance, hints, and explanations.
- Never provide a full solution upfront unless explicitly asked and after several hints.
- Always consider the current problem: "${question?.title || 'Unknown'}"
- Current language: ${selectedLanguage}
- User's current code:
\`\`\`${selectedLanguage}
${currentCode}
\`\`\`
- Keep responses encouraging and professional.
- Use Markdown for all code snippets and formatting.`;

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
            ...messages.slice(-6),
            userMessage
          ],
          max_tokens: 1500,
          temperature: 0.7,
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
        content: `**Error:** ${error.message}. Please check your API key and connection.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReview = () => {
    const reviewPrompt = `Please perform a comprehensive review of my code for the "${question?.title}" problem. 
Check for:
1. Logic errors or potential bugs.
2. Time and space complexity optimizations.
3. Code readability and best practices.
4. How well it handles edge cases.

Provide constructive feedback and hints for improvement.`;
    handleSend(reviewPrompt);
  };

  const clearChat = () => {
    setMessages([initialMessage]);
  };

  const quickActions = [
    { label: 'Hint', prompt: 'Give me a small hint to move forward with this problem.' },
    { label: 'Complexity', prompt: 'Analyze the time and space complexity of my current code.' },
    { label: 'Optimal', prompt: 'What is the most optimal approach for this problem in terms of complexity?' },
    { label: 'Explain', prompt: 'Explain how my current code works step by step.' },
    { label: 'Edge Cases', prompt: 'What are some tricky edge cases I should consider for this problem?' }
  ];

  return (
    <div className="ai-bar">
      <div className="ai-header">
        <div className="ai-title-wrap">
          <h2>AI Coach</h2>
          <span className="model-badge">Llama 3.1 8B</span>
        </div>
        <div className="header-actions">
          <button 
            className="header-btn" 
            onClick={handleReview}
            disabled={isLoading || !currentCode.trim()}
            title="Get a full code review"
          >
            Review
          </button>
          <button 
            className="header-btn secondary" 
            onClick={clearChat}
            disabled={isLoading || messages.length <= 1}
            title="Clear chat history"
          >
            Clear
          </button>
        </div>
      </div>
      
      <div className="ai-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant loading">
            <div className="typing-indicator-wrap">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <span className="typing-text">Coach is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ai-chat-controls">
        <div className="quick-actions">
          {quickActions.map((action) => (
            <button
              key={action.label}
              className="quick-chip"
              onClick={() => handleSend(action.prompt)}
              disabled={isLoading || (action.label !== 'Optimal' && !currentCode.trim())}
            >
              {action.label}
            </button>
          ))}
        </div>
        <div className="input-wrap">
          <textarea 
            placeholder="Ask your coach anything..." 
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
    </div>
  );
};

export default AiBar;
  