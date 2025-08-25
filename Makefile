.PHONY: help install install-frontend install-backend dev dev-frontend dev-backend test test-frontend test-backend lint lint-frontend lint-backend format format-frontend format-backend clean setup

# Default target
help:
	@echo "Available commands:"
	@echo "  setup           - Set up both frontend and backend dependencies"
	@echo "  install         - Install all dependencies"
	@echo "  dev             - Start both frontend and backend in development mode"
	@echo "  test            - Run all tests"
	@echo "  lint            - Run linting for all code"
	@echo "  format          - Format all code"
	@echo "  clean           - Clean build artifacts and caches"
	@echo ""
	@echo "Frontend specific:"
	@echo "  install-frontend - Install frontend dependencies"
	@echo "  dev-frontend     - Start frontend development server"
	@echo "  test-frontend    - Run frontend tests"
	@echo "  lint-frontend    - Lint frontend code"
	@echo "  format-frontend  - Format frontend code"
	@echo ""
	@echo "Backend specific:"
	@echo "  install-backend  - Install backend dependencies"
	@echo "  dev-backend      - Start backend development server"
	@echo "  test-backend     - Run backend tests"
	@echo "  lint-backend     - Lint backend code"
	@echo "  format-backend   - Format backend code"

# Setup and installation
setup: install-backend install-frontend
	@echo "Setup complete!"

install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt

# Development
dev:
	@echo "Starting development servers..."
	@echo "This will start both frontend and backend servers"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	$(MAKE) -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && . venv/bin/activate && python main.py

# Testing
test: test-frontend test-backend

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm run test

test-backend:
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest

# Linting
lint: lint-frontend lint-backend

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

lint-backend:
	@echo "Linting backend code..."
	cd backend && . venv/bin/activate && \
	flake8 . && \
	mypy . && \
	bandit -r . -f json -o bandit-report.json || true

# Formatting
format: format-frontend format-backend

format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format

format-backend:
	@echo "Formatting backend code..."
	cd backend && . venv/bin/activate && \
	black . && \
	isort .

# Type checking
type-check-frontend:
	@echo "Type checking frontend..."
	cd frontend && npm run type-check

type-check-backend:
	@echo "Type checking backend..."
	cd backend && . venv/bin/activate && mypy .

# Pre-commit checks
pre-commit: format lint test
	@echo "Pre-commit checks completed!"

# Cleanup
clean:
	@echo "Cleaning up..."
	cd frontend && rm -rf .next node_modules/.cache coverage htmlcov
	cd backend && rm -rf .pytest_cache htmlcov __pycache__ .coverage .mypy_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Production builds
build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

# Health checks
health-check:
	@echo "Running health checks..."
	@echo "Checking backend health..."
	curl -f http://localhost:8000/health || echo "Backend not responding"
	@echo "Checking frontend..."
	curl -f http://localhost:3000 || echo "Frontend not responding"

# Docker commands (for future use)
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f