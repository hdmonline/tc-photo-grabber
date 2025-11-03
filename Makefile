.PHONY: help install test lint format clean docker-build docker-run docker-stop build

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt pytest black pylint

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	pylint src/

format: ## Format code with black
	black src/

clean: ## Clean cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run: ## Run the application once
	python -m src

run-verbose: ## Run with verbose logging
	python -m src --verbose

run-cron: ## Run in cron mode with daily schedule
	python -m src --cron --schedule daily

dry-run: ## Show what would be downloaded without downloading
	python -m src --dry-run

show-config: ## Display current configuration
	python -m src --show-config

docker-build: ## Build Docker image
	docker build -t tc-photo-grabber:latest .

docker-run: ## Run Docker container once
	docker run --rm -v $(PWD)/photos:/app/photos --env-file .env -e MODE=cli tc-photo-grabber:latest

docker-run-cron: ## Run Docker container in cron mode
	docker run -d --name tc-photo-grabber -v $(PWD)/photos:/app/photos --env-file .env -e MODE=cron -e SCHEDULE=daily tc-photo-grabber:latest

docker-stop: ## Stop and remove Docker container
	docker stop tc-photo-grabber || true
	docker rm tc-photo-grabber || true

docker-logs: ## View Docker container logs
	docker logs -f tc-photo-grabber

compose-up: ## Start with docker-compose
	docker-compose up -d

compose-down: ## Stop docker-compose
	docker-compose down

compose-logs: ## View docker-compose logs
	docker-compose logs -f

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f k8s-deployment.yaml

k8s-delete: ## Delete Kubernetes deployment
	kubectl delete -f k8s-deployment.yaml

k8s-logs: ## View Kubernetes logs
	kubectl logs -f deployment/tc-photo-grabber

build: ## Build Python package
	python setup.py sdist bdist_wheel
