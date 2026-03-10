import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import './CodeEditor.css';

const CodeEditor = ({ question }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('javascript');
  const [code, setCode] = useState({
    javascript: '',
    python: '',
    java: ''
  });

  useEffect(() => {
    if (question && question.starter) {
      setCode({
        javascript: question.starter.javascript || '',
        python: question.starter.python || '',
        java: question.starter.java || ''
      });
    }
  }, [question]);

  const handleEditorChange = (value) => {
    setCode(prev => ({
      ...prev,
      [selectedLanguage]: value
    }));
  };

  const languages = [
    { id: 'python', label: 'Python' },
    { id: 'java', label: 'Java' },
    { id: 'javascript', label: 'JavaScript' }
  ];

  return (
    <div className="code-editor">
      <div className="editor-header">
        {languages.map(lang => (
          <div
            key={lang.id}
            className={`tab ${selectedLanguage === lang.id ? 'active' : ''}`}
            onClick={() => setSelectedLanguage(lang.id)}
          >
            {lang.label}
          </div>
        ))}
      </div>
      <div className="editor-container">
        <Editor
          height="100%"
          language={selectedLanguage}
          value={code[selectedLanguage]}
          theme="vs-dark"
          onChange={handleEditorChange}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: 'on',
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;
