# CodeCoach AI

A comprehensive AI-powered coding assistant that provides real-time code coaching, debugging help, and learning guidance.

## Project Structure

```
CodeCoach-AI/
├── backend/           # FastAPI backend service
├── frontend/          # Next.js frontend application
├── plans/            # Project planning documents
└── shared/           # Shared utilities and types
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
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=sqlite:///./codecoach.db

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379

# Piston (code execution service)
PISTON_API_URL=https://emkc.org/api/v2/piston
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.