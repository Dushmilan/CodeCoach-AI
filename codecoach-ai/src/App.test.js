import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main page components', () => {
  render(<App />);
  const questionHeader = screen.getByText(/Question/i);
  const editorHeader = screen.getByText(/main.js/i);
  const aiHeader = screen.getByText(/AI Assistant/i);
  
  expect(questionHeader).toBeInTheDocument();
  expect(editorHeader).toBeInTheDocument();
  expect(aiHeader).toBeInTheDocument();
});
