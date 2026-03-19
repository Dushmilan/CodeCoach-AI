import React, { useState, useEffect } from 'react';
import './App.css';
import QuestionBar from './components/QuestionBar';
import CodeEditor from './components/CodeEditor';
import AiBar from './components/AiBar';
import questionsData from './data/questions.json';

function App() {
  const [questions] = useState(questionsData);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showQuestionList, setShowQuestionList] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('javascript');
  const [code, setCode] = useState({
    javascript: '',
    python: '',
    java: ''
  });

  const selectedQuestion = questions[currentIndex];

  useEffect(() => {
    if (selectedQuestion && selectedQuestion.starter) {
      setCode({
        javascript: selectedQuestion.starter.javascript || '',
        python: selectedQuestion.starter.python || '',
        java: selectedQuestion.starter.java || ''
      });
    }
  }, [selectedQuestion]);

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % questions.length);
  };

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + questions.length) % questions.length);
  };

  const handleRandom = () => {
    let randomIndex;
    do {
      randomIndex = Math.floor(Math.random() * questions.length);
    } while (randomIndex === currentIndex && questions.length > 1);
    setCurrentIndex(randomIndex);
  };

  const selectQuestion = (index) => {
    setCurrentIndex(index);
    setShowQuestionList(false);
  };

  const handleCodeChange = (newCode) => {
    setCode(prev => ({
      ...prev,
      [selectedLanguage]: newCode
    }));
  };

  return (
    <div className="App">
      <div className="animated-bg">
        <div className="grid-overlay"></div>
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      <div className="main-container">
        <aside className="left-panel">
          <div className="left-panel-header">
            <button 
              className={`problem-list-btn ${showQuestionList ? 'active' : ''}`}
              onClick={() => setShowQuestionList(!showQuestionList)}
            >
              <i className="list-icon">☰</i> Problems
            </button>
            <div className="nav-controls">
              <button onClick={handlePrevious}>&lt;</button>
              <button onClick={handleRandom}>⚄</button>
              <button onClick={handleNext}>&gt;</button>
            </div>
          </div>
          
          <div className="left-panel-content">
            {showQuestionList && (
              <div className="question-list-overlay">
                <div className="question-list">
                  {questions.map((q, index) => (
                    <div 
                      key={q.id} 
                      className={`question-item ${index === currentIndex ? 'active' : ''}`}
                      onClick={() => selectQuestion(index)}
                    >
                      <span className={`dot ${q.difficulty}`}></span>
                      <span className="q-title">{q.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <QuestionBar question={selectedQuestion} />
          </div>
        </aside>
        <main className="center-panel">
          <CodeEditor 
            question={selectedQuestion} 
            selectedLanguage={selectedLanguage}
            setSelectedLanguage={setSelectedLanguage}
            currentCode={code[selectedLanguage]}
            onCodeChange={handleCodeChange}
          />
        </main>
        <aside className="right-panel">
          <AiBar 
            currentCode={code[selectedLanguage]} 
            selectedLanguage={selectedLanguage}
            question={selectedQuestion}
          />
        </aside>
      </div>
    </div>
  );
}

export default App;
