import React, { useState, useRef } from 'react';
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
  const pyodideRef = useRef(null);

  const languages = [
    { id: 'python', label: 'Python' },
    { id: 'java', label: 'Java' },
    { id: 'javascript', label: 'JavaScript' }
  ];

  const runCode = () => {
    setActiveTab('console');
    setHasError(false);
    if (selectedLanguage !== 'javascript') {
      setOutput(`Code execution is currently only supported for JavaScript in this local console. Use "Run Tests" for ${selectedLanguage}.`);
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
      const result = window.eval(currentCode);
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

  const runTests = async () => {
    setActiveTab('tests');
    setShowOutput(true);
    setTestResults([]); 
    
    if (selectedLanguage === 'javascript') {
      runJavaScriptTests();
    } else if (selectedLanguage === 'python') {
      runPythonTestsLocally();
    } else {
      runRemoteTests();
    }
  };

  const runJavaScriptTests = () => {
    const testCases = question.testCases || [];
    const results = [];

    try {
      window.eval(currentCode);

      testCases.forEach((tc, index) => {
        const { input, expected, functionName, inPlace } = tc;
        try {
          const func = window.eval(functionName);
          if (typeof func !== 'function') {
            throw new Error(`${functionName} is not defined. Ensure your function name matches exactly.`);
          }

          const inputClone = JSON.parse(JSON.stringify(input));
          const result = func(...inputClone);
          const actual = inPlace ? inputClone[0] : result;
          const passed = JSON.stringify(actual) === JSON.stringify(expected);

          results.push({ id: index, input: JSON.stringify(input), expected: JSON.stringify(expected), actual: JSON.stringify(actual), passed });
        } catch (err) {
          results.push({ id: index, input: JSON.stringify(input), error: err.message, passed: false });
        }
      });
      setTestResults(results);
    } catch (err) {
      setTestResults([{ error: `Script Error: ${err.message}` }]);
    }
  };

  const runPythonTestsLocally = async () => {
    setOutput('Loading Python environment (Pyodide)...\n');
    const testCases = question.testCases || [];
    const results = [];

    const toPythonValue = (val) => {
      if (val === true) return 'True';
      if (val === false) return 'False';
      if (val === null) return 'None';
      if (Array.isArray(val)) {
        return `[${val.map(toPythonValue).join(', ')}]`;
      }
      return JSON.stringify(val);
    };

    try {
      if (!window.loadPyodide) {
        throw new Error('Pyodide library not found. Ensure you have an internet connection.');
      }
      
      if (!pyodideRef.current) {
        pyodideRef.current = await window.loadPyodide();
      }
      const pyodide = pyodideRef.current;
      setOutput('Python ready. Running tests...\n');

      // Pre-evaluate once to handle errors early and define functions
      try {
        await pyodide.runPythonAsync(currentCode);
      } catch (err) {
        setTestResults([{ error: `Syntax/Runtime Error: ${err.message}` }]);
        return;
      }

      for (let i = 0; i < testCases.length; i++) {
        const tc = testCases[i];
        const { input, expected, pythonFunctionName, inPlace } = tc;
        
        try {
          // Check existence explicitly
          const checkCode = `
import json
try:
    _func = ${pythonFunctionName}
    _exists = True
except NameError:
    _exists = False
`;
          await pyodide.runPythonAsync(checkCode);
          if (!pyodide.globals.get('_exists')) {
            throw new Error(`Function "${pythonFunctionName}" is not defined. Did you rename it?`);
          }

          const pyCode = `
def __run_single_test():
    args = ${toPythonValue(input)}
    expected = ${toPythonValue(expected)}
    in_place = ${inPlace ? 'True' : 'False'}
    
    if in_place:
        input_copy = list(args[0])
        ${pythonFunctionName}(input_copy)
        actual = input_copy
    else:
        actual = ${pythonFunctionName}(*args)
    
    import json
    return json.dumps({"passed": json.dumps(actual) == json.dumps(expected), "actual": actual})

__run_single_test()
          `;
          const rawResult = await pyodide.runPythonAsync(pyCode);
          const res = JSON.parse(rawResult);

          results.push({
            id: i,
            input: JSON.stringify(input),
            expected: JSON.stringify(expected),
            actual: JSON.stringify(res.actual),
            passed: res.passed
          });
        } catch (err) {
          results.push({
            id: i,
            input: JSON.stringify(input),
            error: err.message,
            passed: false
          });
        }
      }
      setTestResults(results);
    } catch (err) {
      setTestResults([{ error: `Python Environment Error: ${err.message}` }]);
    }
  };

  const runRemoteTests = async () => {
    const PISTON_URL = 'https://piston.pensioner.dev/api/v2/execute';
    setOutput('Requesting remote execution (Community Instance)...\n');
    
    const testCases = question.testCases || [];
    let wrapperCode = '';
    let languageId = selectedLanguage;
    let version = '*';

    if (selectedLanguage === 'java') {
      const functionName = testCases[0]?.javaFunctionName;
      const inPlace = testCases[0]?.inPlace;
      
      const toJavaValue = (val) => {
        if (Array.isArray(val)) {
          if (typeof val[0] === 'string') return `new char[]{${val.map(c => `'${c}'`).join(',')}}`;
          return `new int[]{${val.join(',')}}`;
        }
        return JSON.stringify(val);
      };

      const testInvocations = testCases.map((tc, i) => {
        const javaInput = tc.input.map(toJavaValue).join(', ');
        if (inPlace) {
          return `
            try {
                Object input = ${toJavaValue(tc.input[0])};
                sol.${functionName}((${tc.input[0] instanceof Array && typeof tc.input[0][0] === 'string' ? 'char[]' : 'int[]'})input);
                printResult(${i}, ${JSON.stringify(tc.expected)}, input);
            } catch (Exception e) {
                printError(${i}, e.getMessage());
            }
          `;
        } else {
          return `
            try {
                Object actual = sol.${functionName}(${javaInput});
                printResult(${i}, ${JSON.stringify(tc.expected)}, actual);
            } catch (Exception e) {
                printError(${i}, e.getMessage());
            }
          `;
        }
      }).join('\n');

      wrapperCode = `
import java.util.*;

${currentCode}

public class Main {
    public static void main(String[] args) {
        Solution sol = new Solution();
        System.out.println("---RESULTS_START---");
        System.out.print("[");
        ${testInvocations}
        System.out.println("]");
        System.out.println("---RESULTS_END---");
    }

    private static void printResult(int id, Object expected, Object actual) {
        if (id > 0) System.out.print(",");
        String actualStr = formatValue(actual);
        String expectedStr = formatValue(expected);
        boolean passed = actualStr.equals(expectedStr);
        System.out.print(String.format("{\\"passed\\": %b, \\"actual\\": %s, \\"expected\\": %s}", passed, actualStr, expectedStr));
    }

    private static void printError(int id, String msg) {
        if (id > 0) System.out.print(",");
        System.out.print(String.format("{\\"error\\": \\"%s\\", \\"passed\\": false}", msg));
    }

    private static String formatValue(Object val) {
        if (val instanceof char[]) return Arrays.toString((char[])val);
        if (val instanceof int[]) return Arrays.toString((int[])val);
        if (val instanceof String) return "\\"" + val + "\\"";
        if (val instanceof List) return val.toString();
        return String.valueOf(val);
    }
}
`;
    }

    try {
      const response = await fetch(PISTON_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: languageId,
          version: version,
          files: [{ content: wrapperCode }]
        })
      });

      const data = await response.json();
      
      if (!data.run) {
        setTestResults([{ error: `Execution Error: ${data.message || 'Server returned unexpected response.'}` }]);
        return;
      }

      const stdout = data.run.stdout;
      const stderr = data.run.stderr;

      if (stderr) {
        setTestResults([{ error: `Execution Error: ${stderr}` }]);
        return;
      }

      const match = stdout.match(/---RESULTS_START---\n([\s\S]*)\n---RESULTS_END---/);
      if (match) {
        const results = JSON.parse(match[1]);
        setTestResults(results.map((res, i) => ({
          id: i,
          input: JSON.stringify(testCases[i].input),
          expected: JSON.stringify(res.expected),
          actual: JSON.stringify(res.actual),
          passed: res.passed,
          error: res.error
        })));
      } else {
        setOutput(stdout || 'No output from remote runner.');
        setTestResults([{ error: 'Could not parse test results.' }]);
      }
    } catch (err) {
      setTestResults([{ error: `Network Error: ${err.message}` }]);
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
