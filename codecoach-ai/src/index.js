import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));

// Suppress ResizeObserver loop limit exceeded error which is common with Monaco Editor
window.addEventListener('error', e => {
  if (e.message === 'ResizeObserver loop completed with undelivered notifications.' || 
      e.message === 'ResizeObserver loop limit exceeded') {
    const resizeObserverErrGuid = 'f719468e-01be-49b0-9003-f09520445a43';
    if (e.stopImmediatePropagation) {
      e.stopImmediatePropagation();
    }
  }
});

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
