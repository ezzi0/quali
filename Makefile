.PHONY: help setup dev clean test lint format

help:
	@echo "Real Estate AI CRM - Development Commands"
	@echo ""
	@echo "  make setup      - Setup development environment"
	@echo "  make dev        - Start all services with Docker Compose"
	@echo "  make api        - Start API only"
	@echo "  make web        - Start Web only"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make reset-db   - Reset database"

setup:
	@bash scripts/setup_dev.sh

dev:
	cd infra && docker-compose -f docker-compose.dev.yml up

api:
	cd apps/api && uvicorn app.main:app --reload

web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest
	cd apps/web && npm run build

lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

format:
	cd apps/api && ruff format .

clean:
	cd infra && docker-compose -f docker-compose.dev.yml down -v

reset-db:
	@bash scripts/reset_db.sh

