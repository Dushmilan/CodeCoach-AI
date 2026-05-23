import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StructuredResponse } from './StructuredResponse';
import { StructuredCoachingResponse } from '@/types';

const validStructured: StructuredCoachingResponse = {
  summary: 'Great work on the solution!',
  hints: ['Try using a hash map for O(1) lookup', 'Consider edge cases'],
  code_review: 'Your logic is **correct** but could use `early return`',
  complexity_analysis: 'Time: O(n), Space: O(n)',
  suggestions: ['Add input validation', 'Use descriptive variable names'],
  edge_cases: ['Empty input array', 'Single element array'],
  explanation: 'The algorithm works by iterating through the array once.',
  debug_help: 'Check the loop condition on line 5.',
};

describe('StructuredResponse', () => {
  it('renders summary text', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText('Great work on the solution!')).toBeInTheDocument();
  });

  it('renders hints as numbered list', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText('Try using a hash map for O(1) lookup')).toBeInTheDocument();
    expect(screen.getByText('Consider edge cases')).toBeInTheDocument();
  });

  it('renders code review section', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText(/Your logic is/)).toBeInTheDocument();
  });

  it('renders complexity analysis', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText(/O\(n\), Space/)).toBeInTheDocument();
  });

  it('renders suggestions as numbered list', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText('Add input validation')).toBeInTheDocument();
    expect(screen.getByText('Use descriptive variable names')).toBeInTheDocument();
  });

  it('renders edge cases as numbered list', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText('Empty input array')).toBeInTheDocument();
    expect(screen.getByText('Single element array')).toBeInTheDocument();
  });

  it('renders explanation', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText(/iterating through the array/)).toBeInTheDocument();
  });

  it('renders debug help', () => {
    render(<StructuredResponse structured={validStructured} />);
    expect(screen.getByText(/loop condition on line 5/)).toBeInTheDocument();
  });

  it('does not render sections with null values', () => {
    const partial: StructuredCoachingResponse = {
      summary: 'Short summary',
      hints: [],
      code_review: null,
      complexity_analysis: null,
      suggestions: [],
      edge_cases: [],
      explanation: null,
      debug_help: null,
    };
    const { container } = render(<StructuredResponse structured={partial} />);
    expect(screen.getByText('Short summary')).toBeInTheDocument();
    const children = container.firstChild?.childNodes;
    expect(children?.length).toBe(1);
  });

  it('falls back to raw content when structured fails validation', () => {
    const invalid: StructuredCoachingResponse = {
      summary: 'ab',
      hints: [],
      code_review: null,
      complexity_analysis: null,
      suggestions: [],
      edge_cases: [],
      explanation: null,
      debug_help: null,
    };
    render(<StructuredResponse structured={invalid} rawContent="Fallback text" />);
    expect(screen.getByText('Fallback text')).toBeInTheDocument();
  });

  it('returns null when no structured data and no raw content', () => {
    const { container } = render(<StructuredResponse structured={null as unknown as StructuredCoachingResponse} />);
    expect(container.firstChild).toBeNull();
  });

  it('formats bold text with strong tags', () => {
    const bold: StructuredCoachingResponse = {
      ...validStructured,
      code_review: 'This is **very** important',
    };
    const { container } = render(<StructuredResponse structured={bold} />);
    expect(container.querySelector('strong')).toHaveTextContent('very');
  });

  it('formats inline code with code tags', () => {
    const code: StructuredCoachingResponse = {
      ...validStructured,
      code_review: null,
      complexity_analysis: null,
      explanation: 'Use the `map()` function',
    };
    const { container } = render(<StructuredResponse structured={code} />);
    const codeTags = container.querySelectorAll('code');
    const mapCode = Array.from(codeTags).find(c => c.textContent === 'map()');
    expect(mapCode).toBeTruthy();
  });

  it('renders section header lines ending with colon', () => {
    const header: StructuredCoachingResponse = {
      ...validStructured,
      summary: 'Approach:',
    };
    render(<StructuredResponse structured={header} />);
    expect(screen.getByText('Approach:')).toBeInTheDocument();
  });

  it('renders bullet point lines', () => {
    const bullets: StructuredCoachingResponse = {
      ...validStructured,
      summary: '- First bullet\n- Second bullet',
    };
    render(<StructuredResponse structured={bullets} />);
    expect(screen.getByText('First bullet')).toBeInTheDocument();
    expect(screen.getByText('Second bullet')).toBeInTheDocument();
  });
});
