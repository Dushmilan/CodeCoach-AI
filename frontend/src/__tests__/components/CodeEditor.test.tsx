import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CodeEditor } from '../../components/editor/CodeEditor';

// Mock the CodeCoach context
const mockDispatch = jest.fn();
const mockState = {
  code: 'console.log("hello");',
  language: 'javascript',
  currentQuestion: null,
};

jest.mock('../../contexts/CodeCoachContext', () => ({
  useCodeCoach: () => ({
    state: mockState,
    dispatch: mockDispatch,
  }),
}));

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  Editor: ({ onChange, value, language, onMount }: any) => (
    <div data-testid="monaco-editor">
      <textarea
        data-testid="editor-textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-language={language}
      />
      <button data-testid="mount-button" onClick={() => onMount?.({})}>
        Mount Editor
      </button>
    </div>
  ),
}));

describe('CodeEditor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the editor container', () => {
    render(<CodeEditor />);
    
    expect(screen.getByText('Code Editor')).toBeInTheDocument();
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('displays the language selector with correct value', () => {
    render(<CodeEditor />);
    
    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('javascript');
  });

  it('dispatches SET_LANGUAGE when language is changed', () => {
    render(<CodeEditor />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'python' } });
    
    expect(mockDispatch).toHaveBeenCalledWith({
      type: 'SET_LANGUAGE',
      payload: 'python',
    });
  });

  it('dispatches SET_CODE when code changes', () => {
    render(<CodeEditor />);
    
    const textarea = screen.getByTestId('editor-textarea');
    fireEvent.change(textarea, { target: { value: 'const x = 5;' } });
    
    expect(mockDispatch).toHaveBeenCalledWith({
      type: 'SET_CODE',
      payload: 'const x = 5;',
    });
  });

  it('renders reset button', () => {
    render(<CodeEditor />);
    
    expect(screen.getByText('Reset')).toBeInTheDocument();
  });

  it('handles editor mount correctly', () => {
    render(<CodeEditor />);
    
    const mountButton = screen.getByTestId('mount-button');
    fireEvent.click(mountButton);
    
    expect(mountButton).toBeInTheDocument();
  });
});