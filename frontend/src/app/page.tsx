import { Layout } from '@/components/layout/Layout';
import { api } from '@/lib/api';
import { Question } from '@/types';

// Sample questions as fallback
const sampleQuestions: Question[] = [
  {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'Arrays',
    company_tags: ['Google', 'Amazon', 'Meta'],
    description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
    starter: {
      python: 'def two_sum(nums, target):\n # Your code here\n pass',
      javascript: 'function twoSum(nums, target) {\n // Your code here\n}',
      java: 'class Solution {\n public int[] twoSum(int[] nums, int target) {\n // Your code here\n }\n}'
    },
    examples: [
      { input: 'nums = [2,7,11,15], target = 9', output: '[0,1]' },
      { input: 'nums = [3,2,4], target = 6', output: '[1,2]' }
    ],
    test_cases: [
      { input: [[2, 7, 11, 15], 9], expected: [0, 1] },
      { input: [[3, 2, 4], 6], expected: [1, 2] }
    ],
    hints: [
      'Try using a hash map to store the complement of each number',
      'Iterate through the array and check if the complement exists in the hash map'
    ],
    solution: 'Use a hash map to store the complement of each number as you iterate through the array.',
    time_complexity: 'O(n)',
    space_complexity: 'O(n)'
  }
];

async function getQuestions(): Promise<Question[]> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/questions`);
    if (!response.ok) {
      throw new Error('Failed to fetch questions');
    }
    const data = await response.json();
    return data.questions || sampleQuestions;
  } catch (error) {
    console.error('Failed to fetch questions:', error);
    return sampleQuestions;
  }
}

export default async function Home() {
  const questions = await getQuestions();
  
  return <Layout questions={questions} />;
}