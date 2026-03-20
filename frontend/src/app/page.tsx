import { Layout } from '@/components/layout/Layout';
import { api } from '@/lib/api';
import { QuestionSummary } from '@/types';

async function getQuestions(): Promise<QuestionSummary[]> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/questions`, {
      cache: 'no-store'
    });
    if (!response.ok) {
      throw new Error('Failed to fetch questions');
    }
    const data = await response.json();
    return data.questions || [];
  } catch (error) {
    console.error('Failed to fetch questions:', error);
    return [];
  }
}

export default async function Home() {
  const questions = await getQuestions();

  return <Layout questions={questions} />;
}
