# CodeCoach AI - Development Environment Makefile

.PHONY: help install-dev dev clean test lint format build deploy

# Default target
help: ## Show this help message
	@echo "CodeCoach AI Development Environment"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development setup
install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	@if ! command -v pnpm &> /dev/null; then \
		echo "Installing pnpm..."; \
		npm install -g pnpm; \
	fi
	@if ! command -v python3.12 &> /dev/null; then \
		echo "Installing Python 3.12..."; \
		# Windows: winget install Python.Python.3.12 \
		# macOS: brew install python@3.12 \
		# Ubuntu: sudo apt update && sudo apt install python3.12 python3.12-venv; \
	fi
	@echo "Installing monorepo dependencies..."
	@pnpm install
	@echo "Installing backend dependencies..."
	@cd backend && pip install -r requirements.txt
	@echo "Installing pre-commit hooks..."
	@cd backend && pre-commit install
	@echo "Development environment ready!"

dev: ## Start development environment
	@echo "Starting development environment..."
	@docker-compose up -d postgres
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Starting backend..."
	@cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	@cd frontend && pnpm dev &
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"

dev-docker: ## Start development environment with Docker
	@echo "Starting development environment with Docker..."
	@docker-compose up --build

clean: ## Clean development environment
	@echo "Cleaning development environment..."
	@docker-compose down -v
	@docker system prune -f
	@cd frontend && rm -rf .next node_modules
	@cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + || true
	@cd backend && find . -type f -name "*.pyc" -delete || true
	@echo "Development environment cleaned!"

# Testing
test: ## Run all tests
	@echo "Running all tests..."
	@$(MAKE) test-frontend
	@$(MAKE) test-backend

test-frontend: ## Run frontend tests
	@echo "Running frontend tests..."
	@cd frontend && pnpm test

test-backend: ## Run backend tests
	@echo "Running backend tests..."
	@cd backend && pytest tests/ -v

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	@cd backend && pytest tests/ -v --cov=app --cov-report=html
	@cd frontend && pnpm test --coverage

# Linting and formatting
lint: ## Run linting on all packages
	@echo "Running linting..."
	@$(MAKE) lint-frontend
	@$(MAKE) lint-backend

lint-frontend: ## Lint frontend
	@echo "Linting frontend..."
	@cd frontend && pnpm lint

lint-backend: ## Lint backend
	@echo "Linting backend..."
	@cd backend && ruff check .
	@cd backend && mypy app/

format: ## Format all code
	@echo "Formatting code..."
	@$(MAKE) format-frontend
	@$(MAKE) format-backend

format-frontend: ## Format frontend
	@echo "Formatting frontend..."
	@cd frontend && pnpm format

format-backend: ## Format backend
	@echo "Formatting backend..."
	@cd backend && black .
	@cd backend && ruff check . --fix

# Building
build: ## Build all packages
	@echo "Building all packages..."
	@pnpm build

build-frontend: ## Build frontend
	@echo "Building frontend..."
	@cd frontend && pnpm build

build-backend: ## Build backend
	@echo "Building backend..."
	@cd backend && pip install -r requirements.txt

# Deployment
deploy: ## Deploy to production
	@echo "Deploying to production..."
	@$(MAKE) build
	@echo "Deployment complete!"

deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	@$(MAKE) build
	@echo "Staging deployment complete!"

# Database
db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	@cd backend && alembic upgrade head

db-reset: ## Reset database
	@echo "Resetting database..."
	@cd backend && alembic downgrade base && alembic upgrade head

# Supabase
supabase-init: ## Initialize Supabase
	@echo "Initializing Supabase..."
	@supabase init

supabase-start: ## Start Supabase
	@echo "Starting Supabase..."
	@supabase start

supabase-stop: ## Stop Supabase
	@echo "Stopping Supabase..."
	@supabase stop

# Docker
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	@docker-compose build

docker-push: ## Push Docker images
	@echo "Pushing Docker images..."
	@docker-compose push

# Git hooks
install-hooks: ## Install git hooks
	@echo "Installing git hooks..."
	@cd backend && pre-commit install
	@cd frontend && pnpm husky install

# Environment setup
env-setup: ## Setup environment variables
	@echo "Setting up environment variables..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env with your actual values"; \
	else \
		echo ".env file already exists"; \
	fi

# Health checks
health: ## Check health of services
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend not healthy"
	@curl -f http://localhost:3000 || echo "Frontend not healthy"

# Logs
logs: ## Show logs
	@docker-compose logs -f

# Stop all services
stop: ## Stop all services
	@docker-compose down
	@pkill -f "uvicorn" || true
	@pkill -f "next dev" || true