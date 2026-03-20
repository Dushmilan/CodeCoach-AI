import React from 'react';
import { Question } from '@/types';
import { ExampleSection } from './ExampleSection';

interface ExampleContainerProps {
  examples: Question['examples'];
}

export function ExampleContainer({ examples }: ExampleContainerProps) {
  return (
    <>
      {examples.map((example, index) => (
        <ExampleSection key={index} example={example} index={index} />
      ))}
    </>
  );
}