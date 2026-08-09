.PHONY: dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend typecheck build docker-up docker-down clean

# Development
dev:
	docker compose up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && pnpm dev

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest --cov=app --cov-report=term-missing -v

test-backend-unit:
	cd backend && python -m pytest tests/unit/ -v

test-backend-integration:
	cd backend && python -m pytest tests/integration/ -v

test-frontend:
	cd frontend && pnpm test:run

# Vitest requires Node >= 20.12 (styleText); run via a glibc node:20 image
# when the host node is older (host node_modules are reused via mount).
test-frontend-docker:
	docker run --rm -w /app -v "$(PWD)/frontend:/app" node:20 node node_modules/vitest/vitest.mjs run

# Linting & Formatting
lint: lint-backend
	cd frontend && pnpm lint

lint-backend:
	cd backend && ruff check . && ruff format . --check

lint-fix:
	cd backend && ruff check --fix . && ruff format .

# Type Checking
typecheck:
	cd backend && mypy app/
	cd frontend && pnpm typecheck

# Building
build:
	cd frontend && pnpm build

# Docker
docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Cleanup
clean:
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd backend && rm -rf htmlcov .pytest_cache .mypy_cache
	cd frontend && rm -rf .next out
