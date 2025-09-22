# Makefile for Vintern-1B Realtime Demo

.PHONY: help build up down logs clean setup dev prod test

# Default target
help:
	@echo "🎥 Vintern-1B Realtime Demo"
	@echo "Available commands:"
	@echo ""
	@echo "Setup & Build:"
	@echo "  setup     - Initial setup (copy .env, create directories)"
	@echo "  build     - Build all Docker images"
	@echo ""
	@echo "Run & Manage:"
	@echo "  dev       - Start in development mode"
	@echo "  prod      - Start in production mode"  
	@echo "  local     - Start with local model inference"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs      - Show logs from all services"
	@echo "  status    - Show service status"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  reset     - Complete reset (clean + rebuild)"
	@echo ""
	@echo "Model Management:"
	@echo "  convert   - Convert HF model to GGUF format"
	@echo "  download  - Download model from Hugging Face"

# Setup
setup:
	@echo "🔧 Setting up Vintern-1B Demo..."
	@cp -n .env.template .env || echo "⚠️  .env already exists"
	@mkdir -p models logs/backend logs/frontend logs/model-runner logs/nginx
	@echo "✅ Setup complete! Please edit .env file with your configuration."

# Build
build:
	@echo "🏗️  Building Docker images..."
	docker-compose build

# Development
dev: setup
	@echo "🚀 Starting development environment..."
	docker-compose up --build

dev-detached: setup
	@echo "🚀 Starting development environment (background)..."
	docker-compose up -d --build

# Production
prod: setup
	@echo "🏭 Starting production environment..."
	docker-compose --profile production up -d --build

# Local inference mode
local: setup
	@echo "💻 Starting with local model inference..."
	docker-compose --profile local up --build

# Basic operations
up: setup
	docker-compose up -d

down:
	docker-compose down

# Monitoring
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-model:
	docker-compose logs -f model-runner

status:
	@echo "📊 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "🖥️  Resource Usage:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Health checks
health:
	@echo "🏥 Health Check:"
	@curl -s http://localhost:8000/api/health | jq '.' 2>/dev/null || echo "❌ Backend not responding"
	@curl -s http://localhost:3000/health | grep -q "healthy" && echo "✅ Frontend healthy" || echo "❌ Frontend not responding"

# Maintenance
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

reset: clean build
	@echo "🔄 Complete reset done!"

# Model management
convert:
	@echo "🔄 Converting model to GGUF format..."
	@read -p "Enter your Hugging Face token: " HF_TOKEN; \
	docker run --rm -v $(PWD)/models:/models \
		-e HF_TOKEN=$$HF_TOKEN \
		vintern-model-runner \
		python3 /app/convert_model.py --token $$HF_TOKEN

download:
	@echo "⬇️  Downloading model from Hugging Face..."
	@read -p "Enter your Hugging Face token: " HF_TOKEN; \
	docker run --rm -v $(PWD)/models:/models \
		-e HF_TOKEN=$$HF_TOKEN \
		vintern-model-runner \
		python3 /app/convert_model.py --download-only --token $$HF_TOKEN

# Testing
test-backend:
	@echo "🧪 Testing backend..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "🧪 Testing frontend..."
	cd frontend && npm test -- --watchAll=false

test: test-backend test-frontend

# Shortcuts
start: up
stop: down
restart: down up
rebuild: down build up

# Development helpers
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

shell-model:
	docker-compose exec model-runner bash

# Backup and restore
backup:
	@echo "💾 Creating backup..."
	@tar -czf vintern-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=node_modules \
		--exclude=__pycache__ \
		--exclude=.git \
		--exclude=models \
		--exclude=logs \
		.
	@echo "✅ Backup created!"

# Environment validation
validate-env:
	@echo "✅ Validating environment..."
	@test -f .env || (echo "❌ .env file not found! Run 'make setup' first." && exit 1)
	@grep -q "HF_TOKEN=" .env || echo "⚠️  HF_TOKEN not set in .env"
	@grep -q "MODEL_MODE=" .env || echo "⚠️  MODEL_MODE not set in .env"
	@echo "✅ Environment validation complete!"

# Quick start guides
quickstart-hf:
	@echo "🚀 Quick Start - Hugging Face Mode"
	@echo "1. Copy .env template: cp .env.template .env"
	@echo "2. Edit .env and add your HF_TOKEN"
	@echo "3. Run: make dev"
	@echo "4. Open: http://localhost:3000"

quickstart-local:
	@echo "🚀 Quick Start - Local Mode"
	@echo "1. Run: make setup"
	@echo "2. Convert model: make convert"
	@echo "3. Edit .env: set MODEL_MODE=local"
	@echo "4. Run: make local"
	@echo "5. Open: http://localhost:3000"

# Show URLs
urls:
	@echo "🌐 Application URLs:"
	@echo "Frontend:    http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs:    http://localhost:8000/docs"
	@echo "Health:      http://localhost:8000/api/health"