import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import './CodeEditor.css';

const CodeEditor = ({ 
  question,
  selectedLanguage, 
  setSelectedLanguage, 
  currentCode, 
  onCodeChange 
}) => {
  const [output, setOutput] = useState('');
  const [showOutput, setShowOutput] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [activeTab, setActiveTab] = useState('console'); // 'console' or 'tests'
  const [testResults, setTestResults] = useState([]);

  const languages = [
    { id: 'python', label: 'Python' },
    { id: 'java', label: 'Java' },
    { id: 'javascript', label: 'JavaScript' }
  ];

  const runCode = () => {
    setActiveTab('console');
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

  const runTests = () => {
    setActiveTab('tests');
    setShowOutput(true);
    if (selectedLanguage !== 'javascript') {
      setTestResults([{ error: 'Testing is only supported for JavaScript.' }]);
      return;
    }

    const testCases = question.testCases || [];
    const results = [];

    try {
      // Use window.eval to ensure declarations are made in the global scope.
      // This bypasses the strict mode isolation of the React component.
      window.eval(currentCode);

      testCases.forEach((tc, index) => {
        const { input, expected, functionName, inPlace } = tc;
        
        try {
          // Look up the function in the global scope
          const func = window.eval(functionName);
          if (typeof func !== 'function') {
            throw new Error(`${functionName} is not defined. Ensure your function name matches exactly.`);
          }

          // Clone input for in-place checks
          const inputClone = JSON.parse(JSON.stringify(input));
          const result = func(...inputClone);
          
          const actual = inPlace ? inputClone[0] : result;
          const passed = JSON.stringify(actual) === JSON.stringify(expected);

          results.push({
            id: index,
            input: JSON.stringify(input),
            expected: JSON.stringify(expected),
            actual: JSON.stringify(actual),
            passed
          });
        } catch (err) {
          results.push({
            id: index,
            input: JSON.stringify(input),
            error: err.message,
            passed: false
          });
        }
      });
      setTestResults(results);
    } catch (err) {
      setTestResults([{ error: `Script Error: ${err.message}` }]);
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
          <button className="run-btn secondary" onClick={runCode}>
            Console
          </button>
          <button className="run-btn" onClick={runTests}>
            <i className="play-icon">▶</i> Run Tests
          </button>
        </div>
      </div>
      <div className="editor-container-main">
        <div className="editor-container" style={{ height: showOutput ? '65%' : '100%' }}>
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
          <div className={`output-panel ${activeTab === 'console' ? (hasError ? 'error' : 'success') : ''}`}>
            <div className="output-header">
              <div className="tab-buttons">
                <button 
                  className={`tab-btn ${activeTab === 'console' ? 'active' : ''}`}
                  onClick={() => setActiveTab('console')}
                >
                  Console
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'tests' ? 'active' : ''}`}
                  onClick={() => setActiveTab('tests')}
                >
                  Test Results
                </button>
              </div>
              <div className="output-actions">
                {activeTab === 'console' && (
                  <button className="clear-output" onClick={() => setOutput('')}>Clear</button>
                )}
                <button className="close-output" onClick={() => setShowOutput(false)}>×</button>
              </div>
            </div>
            
            <div className="output-body">
              {activeTab === 'console' ? (
                <pre className="output-content">
                  {output}
                </pre>
              ) : (
                <div className="test-results">
                  {testResults.map((res, i) => (
                    <div key={i} className={`test-item ${res.passed ? 'pass' : 'fail'}`}>
                      <div className="test-status-line">
                        <span className="status-badge">{res.passed ? '✓ PASS' : '✗ FAIL'}</span>
                        <span className="test-name">Test Case {i + 1}</span>
                      </div>
                      {res.error ? (
                        <div className="test-error">{res.error}</div>
                      ) : (
                        <div className="test-details">
                          <div><span className="label">Input:</span> <code>{res.input}</code></div>
                          {!res.passed && (
                            <>
                              <div><span className="label">Expected:</span> <code className="expected">{res.expected}</code></div>
                              <div><span className="label">Actual:</span> <code className="actual">{res.actual}</code></div>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {testResults.length === 0 && <div className="no-tests">Click "Run Tests" to see results.</div>}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CodeEditor;
