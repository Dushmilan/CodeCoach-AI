import React from 'react';
import './App.css';
import QuestionBar from './components/QuestionBar';
import CodeEditor from './components/CodeEditor';
import AiBar from './components/AiBar';

function App() {
  return (
    <div className="App">
      <div className="main-container">
        <aside className="left-panel">
          <QuestionBar />
        </aside>
        <main className="center-panel">
          <CodeEditor />
        </main>
        <aside className="right-panel">
          <AiBar />
        </aside>
      </div>
    </div>
  );
}

export default App;
