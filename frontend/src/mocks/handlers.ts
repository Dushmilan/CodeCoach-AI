import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/questions/', () => {
    return HttpResponse.json({ questions: [], total: 0 });
  }),
  http.get('/api/questions/stats', () => {
    return HttpResponse.json({ total: 0, by_difficulty: {}, by_category: {} });
  }),
  http.get('/api/questions/categories', () => {
    return HttpResponse.json({ categories: [] });
  }),
  http.get('/api/questions/companies', () => {
    return HttpResponse.json({ companies: [] });
  }),
  http.get('/api/run/languages', () => {
    return HttpResponse.json({ languages: [] });
  }),
  http.post('/api/auth/login', () => {
    return HttpResponse.json({
      access_token: 'test-token',
      expires_in: 86400,
      user: { id: '1', username: 'testuser', email: 'test@test.com' },
    });
  }),
  http.post('/api/auth/register', () => {
    return HttpResponse.json({
      access_token: 'test-token',
      expires_in: 86400,
      user: { id: '1', username: 'newuser', email: 'new@test.com' },
    });
  }),
  http.get('/api/auth/me', () => {
    return HttpResponse.json({ id: '1', username: 'testuser', email: 'test@test.com' });
  }),
  http.post('/api/run/', () => {
    return HttpResponse.json({
      stdout: 'Hello\n', stderr: '', exit_code: 0,
      language: 'python', version: '3.10.0',
    });
  }),
  http.post('/api/coach/', () => {
    return HttpResponse.json({
      response: 'Here is a hint...',
      mode: 'hint', language: 'python',
    });
  }),
  http.get('/health', () => {
    return HttpResponse.json({ status: 'healthy' });
  }),
  http.get('/api/courses/', () => {
    return HttpResponse.json({
      courses: [
        { id: '1', title: 'Test Course', description: 'A test course', module_count: 1 },
      ],
    });
  }),
  http.get('/api/courses/:courseId', ({ params }) => {
    return HttpResponse.json({
      id: params.courseId, title: 'Test Course', description: 'A test course',
      modules: [],
    });
  }),
  http.get('/api/courses/lessons/:lessonId', ({ params }) => {
    return HttpResponse.json({
      id: params.lessonId, title: 'Test Lesson', description: 'A test lesson',
      content: 'Lesson content', type: 'theory',
    });
  }),
];
