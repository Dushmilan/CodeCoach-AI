import React from 'react';
import './CodeEditor.css';

const CodeEditor = () => {
  return (
    <div className="code-editor">
      <div className="editor-header">
        <span>main.js</span>
      </div>
      <textarea 
        className="editor-textarea" 
        placeholder="// Write your code here..."
        defaultValue={`function solution() {\n  // Start coding\n}`}
      />
    </div>
  );
};

export default CodeEditor;
