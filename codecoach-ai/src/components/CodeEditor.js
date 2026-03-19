import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import './CodeEditor.css';

const CodeEditor = ({ 
  selectedLanguage, 
  setSelectedLanguage, 
  currentCode, 
  onCodeChange 
}) => {
  const [output, setOutput] = useState('');
  const [showOutput, setShowOutput] = useState(false);
  const [hasError, setHasError] = useState(false);

  const languages = [
    { id: 'python', label: 'Python' },
    { id: 'java', label: 'Java' },
    { id: 'javascript', label: 'JavaScript' }
  ];

  const runCode = () => {
    setHasError(false);
    if (selectedLanguage !== 'javascript') {
      setOutput('Code execution is currently only supported for JavaScript in this prototype.');
      setShowOutput(true);
      setHasError(true);
      return;
    }

    setOutput('Running...\n');
    setShowOutput(true);

    const originalLog = console.log;
    let logs = [];
    console.log = (...args) => {
      logs.push(args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' '));
    };

    try {
      const result = eval(currentCode);
      if (result !== undefined) {
        logs.push(`=> ${typeof result === 'object' ? JSON.stringify(result, null, 2) : result}`);
      }
      setOutput(logs.join('\n') || 'Program finished with no output.');
    } catch (err) {
      setHasError(true);
      setOutput(`Runtime Error: ${err.message}`);
    } finally {
      console.log = originalLog;
    }
  };

  return (
    <div className="code-editor">
      <div className="editor-header">
        <div className="language-selector">
          <label htmlFor="language-select">Language:</label>
          <select 
            id="language-select"
            value={selectedLanguage} 
            onChange={(e) => setSelectedLanguage(e.target.value)}
          >
            {languages.map(lang => (
              <option key={lang.id} value={lang.id}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>
        <div className="editor-actions">
          <button className="run-btn" onClick={runCode}>
            <i className="play-icon">▶</i> Run Code
          </button>
        </div>
      </div>
      <div className="editor-container-main">
        <div className="editor-container" style={{ height: showOutput ? '70%' : '100%' }}>
          <Editor
            height="100%"
            language={selectedLanguage}
            value={currentCode}
            theme="vs-dark"
            onChange={onCodeChange}
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
        {showOutput && (
          <div className={`output-panel ${hasError ? 'error' : 'success'}`}>
            <div className="output-header">
              <div className="output-status">
                <span className="status-dot"></span>
                <span>{hasError ? 'Runtime Error' : 'Console Output'}</span>
              </div>
              <div className="output-actions">
                <button className="clear-output" onClick={() => setOutput('')}>Clear</button>
                <button className="close-output" onClick={() => setShowOutput(false)}>×</button>
              </div>
            </div>
            <pre className="output-content">
              {output}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default CodeEditor;
