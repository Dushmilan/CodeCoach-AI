import React, { useState } from 'react';
import './App.css';
import QuestionBar from './components/QuestionBar';
import CodeEditor from './components/CodeEditor';
import AiBar from './components/AiBar';
import questionsData from './data/questions.json';

function App() {
  const [questions] = useState(questionsData);
  const [selectedQuestion, setSelectedQuestion] = useState(questions[0]);

  return (
    <div className="App">
      <div className="main-container">
        <aside className="left-panel">
          <QuestionBar question={selectedQuestion} />
        </aside>
        <main className="center-panel">
          <CodeEditor question={selectedQuestion} />
        </main>
        <aside className="right-panel">
          <AiBar />
        </aside>
      </div>
    </div>
  );
}

export default App;
