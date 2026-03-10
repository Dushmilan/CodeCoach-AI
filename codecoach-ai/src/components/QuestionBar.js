import React from 'react';
import './QuestionBar.css';

const QuestionBar = ({ question }) => {
  if (!question) return <div className="question-bar">Loading...</div>;

  return (
    <div className="question-bar">
      <div className="question-header">
        <h2>{question.title}</h2>
        <div className="question-meta">
          <span className={`difficulty ${question.difficulty}`}>{question.difficulty}</span>
          <span className="category">{question.category}</span>
        </div>
      </div>
      <div className="question-content">
        <p className="description">{question.description}</p>
        
        <h3>Examples:</h3>
        {question.examples.map((example, index) => (
          <div key={index} className="example">
            <p><strong>Input:</strong> {example.input}</p>
            <p><strong>Output:</strong> {example.output}</p>
          </div>
        ))}

        {question.hints && question.hints.length > 0 && (
          <>
            <h3>Hints:</h3>
            <ul>
              {question.hints.map((hint, index) => (
                <li key={index}>{hint}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
};

export default QuestionBar;
