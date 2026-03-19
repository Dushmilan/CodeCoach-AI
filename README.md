# CodeCoach AI - Cloud-Native Development Environment

A comprehensive, fully automated cloud-native development environment featuring a Next.js 14 frontend with Edge Runtime and a FastAPI Python 3.12 backend with strict mypy typing.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ with pnpm
- Python 3.12+ with pip
- Docker Desktop (for containerized services)
- Git

### One-Command Setup
```bash
# Clone and setup everything
make install-dev

# Start development environment
make dev
```

### Manual Setup
```bash
# Install dependencies
pnpm install
cd backend && pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your actual values

# Start services
docker-compose up -d postgres
pnpm dev
```

## 📁 Project Structure

```
codecoach-ai/
├── frontend/                 # Next.js 14 TypeScript app (Edge Runtime)
│   ├── src/app/             # App Router
│   ├── components/          # React components
│   ├── lib/                # Utility functions
│   └── public/             # Static assets
├── backend/                 # FastAPI Python 3.12 service
│   ├── app/                # FastAPI application
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Pydantic models
│   │   └── db/             # Database setup
│   ├── tests/              # Pytest test suite
│   └── Dockerfile          # Multi-stage container
├── packages/               # Shared packages
├── .github/                # GitHub Actions & settings
├── supabase/              # Supabase migrations
├── docker-compose.yml     # Development services
├── render.yaml            # Render deployment blueprint
└── Makefile              # Development commands
```

## 🛠️ Technology Stack

### Frontend
- **Runtime**: Next.js 14 with Edge Runtime
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Testing**: Jest + React Testing Library

### Backend
- **Runtime**: Python 3.12
- **Framework**: FastAPI with strict mypy
- **Database**: PostgreSQL with pgvector
- **ORM**: SQLAlchemy 2.0 (async)
- **Testing**: pytest with pytest-asyncio

### Infrastructure
- **Package Manager**: pnpm with workspace support
- **Build System**: Turborepo
- **Container**: Docker multi-stage builds
- **Deployment**: Vercel (frontend) + Render (backend)
- **CI/CD**: GitHub Actions

## 🚦 Development Workflow

### Available Commands

```bash
# Development
make install-dev      # Install all dependencies
make dev             # Start development environment
make dev-docker      # Start with Docker Compose
make clean           # Clean development environment

# Testing
make test            # Run all tests
make test-frontend   # Run frontend tests
make test-backend    # Run backend tests
make test-coverage   # Run tests with coverage

# Code Quality
make lint            # Lint all code
make format          # Format all code

# Building
make build           # Build all packages
make build-frontend  # Build frontend
make build-backend   # Build backend

# Database
make db-migrate      # Run migrations
make db-reset        # Reset database

# Supabase
make supabase-start  # Start Supabase
make supabase-stop   # Stop Supabase

# Docker
make docker-build    # Build Docker images
make docker-push     # Push Docker images

# Deployment
make deploy          # Deploy to production
make deploy-staging  # Deploy to staging
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/codecoach_ai
SECRET_KEY=your-secret-key
ENVIRONMENT=development

# External APIs
NVIDIA_API_KEY=
OPENAI_API_KEY=
```

## 🌐 Services

### Development URLs
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Supabase Studio**: http://localhost:54323

### Docker Services
- **PostgreSQL**: localhost:5432
- **ngrok**: http://localhost:4040

## 🚀 Deployment

### Vercel (Frontend)
Automatic deployment from `main` branch with preview URLs for PRs.

### Render (Backend)
Automatic deployment from `main` branch with zero-downtime deployments.

### GitHub Actions
- **CI/CD**: Automated testing and deployment
- **Security**: Snyk and Trivy vulnerability scanning
- **Preview**: PR preview deployments

## 🔒 Security

- **Branch Protection**: Main branch requires 2 PR reviews
- **Secrets**: Managed via GitHub Environments
- **Scanning**: Automated security scanning
- **CORS**: Configured for production domains

## 📊 Monitoring

- **Health Checks**: `/health` endpoint
- **Logging**: Structured JSON logging
- **Metrics**: Prometheus metrics
- **Error Tracking**: Sentry integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `make test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/codecoach-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/codecoach-ai/discussions)
- **Documentation**: [API Docs](https://your-api-docs-url.com)
