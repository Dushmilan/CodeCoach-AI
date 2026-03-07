import React from 'react';
import './QuestionBar.css';

const QuestionBar = () => {
  return (
    <div className="question-bar">
      <h2>Question</h2>
      <div className="question-content">
        <p>Your coding challenge will appear here. Solve the problem by writing code in the editor.</p>
      </div>
    </div>
  );
};

export default QuestionBar;
