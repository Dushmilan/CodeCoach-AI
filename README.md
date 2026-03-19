# CodeCoach AI - Full Stack Implementation

## Overview
CodeCoach AI is an AI-powered coding interview practice platform that provides real-time coaching and code execution capabilities. This is the Phase 2 full-stack implementation.

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   NVIDIA NIM    │
│   Frontend      │◄──►│   Backend       │◄──►│   AI Coaching   │
│   (Vercel)      │    │   (Render)      │    │   (Free Tier)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Piston API    │
                       │   Code Exec     │
                       └─────────────────┘
```

## Project Structure
```
codecoach-ai/
├── frontend/          # Next.js 14 application
│   ├── src/
│   │   ├── app/       # App Router
│   │   ├── components/ # React components
│   │   └── lib/       # Utilities and types
│   ├── package.json
│   └── next.config.js
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── models/    # Pydantic models
│   │   └── services/  # Business logic
│   ├── questions/     # Question bank JSON files
│   ├── requirements.txt
│   └── Dockerfile
├── shared/            # Shared types and utilities
└── plans/             # Implementation plans
```

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- NVIDIA NIM API key (free from build.nvidia.com)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your NVIDIA API key

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install

# Copy environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Run development server
npm run dev
```

## Features
- **AI Coaching**: Real-time hints and code review via NVIDIA NIM
- **Code Execution**: Multi-language support via Piston API
- **Progress Tracking**: User authentication and progress persistence
- **Responsive Design**: Mobile-first responsive design
- **Zero Cost**: Deployed on free tiers of Vercel, Render, and Supabase

## API Endpoints
- `POST /api/coach` - AI coaching proxy
- `POST /api/run` - Code execution
- `GET /api/questions` - List all questions
- `GET /api/questions/:id` - Get specific question
- `GET /health` - Health check

## Environment Variables

### Backend (.env)
```bash
NVIDIA_API_KEY=your_nvidia_nim_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
PORT=8000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Deployment

### Vercel (Frontend)
1. Connect GitHub repository to Vercel
2. Set environment variables
3. Deploy automatically on push to main

### Render (Backend)
1. Create new web service
2. Use Dockerfile for deployment
3. Set environment variables
4. Deploy automatically on push to main

### Supabase (Database & Auth)
1. Create new Supabase project
2. Run database migrations
3. Configure GitHub OAuth
4. Set up row-level security

## Development

### Adding New Questions
Add JSON files to `backend/questions/` following the schema:
```json
{
  "id": "two-sum",
  "title": "Two Sum",
  "difficulty": "easy",
  "category": "Arrays",
  "description": "...",
  "starter": {
    "python": "...",
    "javascript": "...",
    "java": "..."
  },
  "test_cases": [...]
}
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License
MIT License - see LICENSE file for details