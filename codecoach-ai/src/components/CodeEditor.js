import React from 'react';
import Editor from '@monaco-editor/react';
import './CodeEditor.css';

const CodeEditor = () => {
  const handleEditorChange = (value) => {
    // This is where you can handle the code content as it changes
    console.log('Editor content:', value);
  };

  return (
    <div className="code-editor">
      <div className="editor-header">
        <span>main.js</span>
      </div>
      <div className="editor-container" style={{ flex: 1, height: '100%' }}>
        <Editor
          height="100%"
          defaultLanguage="javascript"
          defaultValue={`function solution() {\n  // Start coding\n}`}
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
