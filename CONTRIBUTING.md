# Contributing to CodeCoach AI

Thanks for your interest in contributing! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Coding Conventions](#coding-conventions)
- [Issue Labels](#issue-labels)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/CodeCoach-AI.git
   cd CodeCoach-AI
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/dushmilan/CodeCoach-AI.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Quick Start with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

#### Piston (Code Execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

### Environment Variables

Copy `.env.example` to `.env` in the backend directory and fill in:

```
NVIDIA_API_KEY=your_nvidia_nim_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
JWT_SECRET_KEY=your_jwt_secret_key
```

Get free API keys from:

- [NVIDIA NIM](https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct)
- [Google Gemini](https://aistudio.google.com/apikey)

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-new-language` — new features
- `fix/resolve-login-bug` — bug fixes
- `docs/update-readme` — documentation
- `refactor/clean-coach-service` — refactoring
- `test/add-question-tests` — adding tests

### Commit Messages

Write clear, concise commit messages:

```
Add dark mode toggle to settings

- Add ThemeToggle component
- Persist preference in localStorage
- Update ThemeProvider context
```

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest                      # All tests
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest --cov=app            # With coverage
```

### Frontend (Vitest)

```bash
cd frontend
npm test                              # Watch mode
npm run test:run                      # Single run
npm run lint                          # ESLint
npm run typecheck                     # TypeScript check
```

### Before Submitting

Run all checks before submitting your PR:

```bash
# Backend
cd backend
ruff check .
ruff format . --check
python -m pytest

# Frontend
cd frontend
npm run typecheck
npm run lint
npm run test:run
```

## Submitting a Pull Request

1. **Update your fork**:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a PR** on GitHub with:

   - Clear title describing the change
   - Description of what changed and why
   - Link to related issue (e.g., "Fixes #42")
   - Screenshots for UI changes

4. **Respond to review feedback** — maintainers may request changes

5. **Squash commits** if asked before merging

## Coding Conventions

### General

- **No comments** unless logic is genuinely non-obvious
- **Named exports** over default exports
- **Async everywhere** — handlers, services, use cases
- **No secrets in code** — API keys from headers/env vars only

### Backend (Python)

- Full type annotations
- Pydantic v2 schemas
- Module-level loggers
- `snake_case` for functions/variables
- FastAPI `Depends()` for DI
- Every language needs a code wrapper in `adapters/code_wrappers/`

### Frontend (TypeScript)

- Strict mode, no `any`
- `import type` for type-only imports
- `PascalCase` components, `camelCase` functions
- Tailwind CSS only (no CSS modules, no styled-components)
- Feature-based organization (`features/{name}/{hook,service,types}`)

### File Structure

Follow existing patterns:

```
backend/app/
  api/            # Thin route handlers
  services/       # Business logic
  use_cases/      # Validation logic
  models/         # Pydantic schemas
  ports/          # Abstract interfaces
  adapters/       # Concrete implementations

frontend/src/
  features/       # Feature modules
  components/     # Reusable UI
  hooks/          # Shared hooks
  lib/            # Utilities
```

## Issue Labels

| Label              | Description                |
| ------------------ | -------------------------- |
| `good first issue` | Great for newcomers        |
| `help wanted`      | Extra attention needed     |
| `bug`              | Something isn't working    |
| `enhancement`      | New feature or request     |
| `documentation`    | Improvements to docs       |
| `question`         | Further information needed |

## Questions?

Open a [GitHub Discussion](https://github.com/dushmilan/CodeCoach-AI/discussions) or check the [README](README.md).
