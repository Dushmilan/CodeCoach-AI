# CodeCoach AI

A comprehensive AI-powered coding assistant that provides real-time code coaching, debugging help, and learning guidance.

## Project Structure

```
CodeCoach-AI/
├── backend/           # FastAPI backend service
│   ├── app/
│   │   ├── api/       # API endpoints (coach, health, questions, run, validation)
│   │   ├── middleware/# Rate limiting middleware
│   │   ├── models/    # Pydantic schemas
│   │   └── services/  # Business logic (NIM, Piston, validators)
│   ├── tests/         # Comprehensive test suite
│   └── questions/     # Sample coding questions
├── frontend/          # Next.js frontend application
│   └── src/
│       ├── app/       # Next.js app router
│       ├── components/# React components (chat, editor, layout)
│       ├── lib/       # API utilities
│       └── types/     # TypeScript types
├── plans/             # Project planning documents
└── shared/            # Shared utilities and types
```

## Quick Start

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables:**
```bash
cp .env.example .env
```
Edit `.env` with your actual configuration values.

6. **Start the backend server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
# or
pnpm install
# or
yarn install
```

3. **Set up environment variables:**
```bash
cp .env.example .env.local
```
Edit `.env.local` with your actual configuration values.

4. **Start the development server:**
```bash
npm run dev
# or
pnpm dev
# or
yarn dev
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## Development Commands

### Backend
- `uvicorn app.main:app --reload` - Start with auto-reload
- `python -m pytest` - Run tests
- `python -m black .` - Format code
- `python -m flake8` - Lint code

### Frontend
- `npm run dev` - Development server
- `npm run build` - Production build
- `npm start` - Production server
- `npm run lint` - Lint code

## Environment Variables

### Backend (.env)
```
# API Keys
NVIDIA_API_KEY=your_nvidia_nim_api_key

# Database
DATABASE_URL=sqlite:///./codecoach.db

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379

# Piston (code execution service)
# Use public instance:
PISTON_API_URL=https://emkc.org/api/v2/piston
# Or local instance (recommended for development):
# PISTON_API_URL=http://localhost:2000/api/v2/piston
```

**Note:** The `NVIDIA_API_KEY` is required for AI coaching features. Get your free API key from [NVIDIA NIM](https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct).

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Local Piston Setup (Optional)

For faster code execution during development, you can run Piston locally:

1. **Install Piston via Docker:**
```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

2. **Update your `.env` file:**
```
PISTON_API_URL=http://localhost:2000/api/v2/piston
```

3. **Verify Piston is running:**
```bash
curl http://localhost:2000/api/v2/runtimes
```

4. **Test code execution:**
```bash
curl -X POST http://localhost:2000/api/v2/execute \
  -H "Content-Type: application/json" \
  -d '{"language":"python","version":"*","files":[{"name":"test.py","content":"print(\"Hello from Piston!\")"}]}'
```

## Docker Setup (Optional)

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Access the application:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Features

- **Real-time Code Coaching:** Get instant feedback on your code
- **Multi-language Support:** Support for Python, JavaScript, TypeScript, and more
- **Interactive Debugging:** Step-by-step debugging assistance
- **Learning Paths:** Personalized coding challenges and tutorials
- **Code Execution:** Safe code execution in sandboxed environment
- **Progress Tracking:** Monitor your learning progress

## Recent Improvements

### Code Validation System
- **Simple Validators:** Added lightweight validators for Python, JavaScript, and Java that run test cases locally
- **Output Comparison:** Smart output matching supporting string, JSON, and numeric comparisons
- **Error Handling:** User-friendly error messages with emoji indicators for different error types

### Test Suite
- **Comprehensive Testing:** Production-grade test suite covering functional, boundary, load, and security tests
- **Test Categories:**
  - Unit tests for validators and boundary conditions
  - Integration tests for all API endpoints
  - Performance tests for concurrent request handling
  - Security tests for injection prevention (SQL, XSS, command, path traversal)
- **Test Utilities:** Factory fixtures for generating test data

### API Enhancements
- **Rate Limiting:** Middleware for API rate limiting to prevent abuse
- **Health Endpoints:** Detailed health checks for monitoring
- **Validation Endpoints:** Pre-execution code validation without running code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
