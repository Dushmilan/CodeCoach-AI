import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LessonChrome } from './LessonChrome';
import { LessonSummary } from '@/types';

const lesson: LessonSummary = {
  id: 'l1',
  course_id: 'c1',
  module_id: 'm1',
  title: 'Variables',
  type: 'theory',
  content: 'content',
  order: 1,
  starter_code: null,
  test_cases: null,
  question_id: null,
  language: 'python',
};

describe('LessonChrome', () => {
  it('renders lesson title and type', () => {
    render(<LessonChrome lesson={lesson} prevId={null} nextId={null} />);
    expect(screen.getByText('Variables')).toBeInTheDocument();
    expect(screen.getByText('Theory Lesson')).toBeInTheDocument();
  });

  it('renders exercise badge for exercise lessons', () => {
    render(<LessonChrome lesson={{ ...lesson, type: 'exercise' }} prevId={null} nextId={null} />);
    expect(screen.getByText('Coding Exercise')).toBeInTheDocument();
  });

  it('links back to the course', () => {
    render(<LessonChrome lesson={lesson} prevId={null} nextId={null} />);
    const back = screen.getByRole('link', { name: /Back/ });
    expect(back).toHaveAttribute('href', '/learn/c1');
  });
});
