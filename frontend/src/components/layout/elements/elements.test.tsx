import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MainLayoutContainer } from './MainLayoutContainer';
import { MainContentContainer } from './MainContentContainer';
import { ContentLayoutContainer } from './ContentLayoutContainer';
import { QuestionContentSection } from './QuestionContentSection';
import { LoadingSkeleton } from './LoadingSkeleton';

describe('MainLayoutContainer', () => {
  it('renders children', () => {
    render(<MainLayoutContainer><p>content</p></MainLayoutContainer>);
    expect(screen.getByText('content')).toBeInTheDocument();
  });

  it('renders as a main element with correct role', () => {
    render(<MainLayoutContainer>test</MainLayoutContainer>);
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});

describe('MainContentContainer', () => {
  it('renders children', () => {
    render(<MainContentContainer><span>child</span></MainContentContainer>);
    expect(screen.getByText('child')).toBeInTheDocument();
  });
});

describe('ContentLayoutContainer', () => {
  it('renders children', () => {
    render(<ContentLayoutContainer><div>child</div></ContentLayoutContainer>);
    expect(screen.getByText('child')).toBeInTheDocument();
  });
});

describe('QuestionContentSection', () => {
  it('renders children', () => {
    render(<QuestionContentSection><article>content</article></QuestionContentSection>);
    expect(screen.getByText('content')).toBeInTheDocument();
  });

  it('renders as a section with aria label', () => {
    render(<QuestionContentSection>test</QuestionContentSection>);
    expect(screen.getByRole('region')).toBeInTheDocument();
  });
});

describe('LoadingSkeleton', () => {
  it('renders skeleton placeholder elements', () => {
    const { container } = render(<LoadingSkeleton />);
    const skeletonElements = container.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThanOrEqual(3);
  });
});
