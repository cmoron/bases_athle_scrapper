.PHONY: help install test coverage lint format check clean

help: ## Affiche l'aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances de dev
	pip install -r requirements-dev.txt

test: ## Lance les tests
	pytest -v

coverage: ## Lance les tests avec coverage
	pytest --cov --cov-report=term-missing --cov-report=html
	@echo "📊 Rapport HTML généré dans htmlcov/index.html"

lint: ## Vérifie la qualité du code (ruff + mypy)
	@echo "🔍 Linting avec ruff..."
	ruff check .
	@echo "\n🔍 Type checking avec mypy..."
	mypy scraper/ core/ tools/ --ignore-missing-imports

format: ## Formate le code avec black
	@echo "✨ Formatage avec black..."
	black .
	@echo "📦 Organisation des imports avec ruff..."
	ruff check --fix --select I .

check: lint test ## Lance tous les checks (lint + tests)

fix: format ## Fixe automatiquement les problèmes de formatage
	ruff check --fix .

clean: ## Nettoie les fichiers temporaires
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

ci: ## Simule la CI en local
	@echo "🚀 Simulation de la CI..."
	@echo "\n📝 1. Vérification formatage black..."
	black --check --diff . || (echo "❌ Formatage incorrect" && exit 1)
	@echo "\n✅ Formatage OK"
	@echo "\n🔍 2. Linting ruff..."
	ruff check . || (echo "❌ Linting échoué" && exit 1)
	@echo "\n✅ Linting OK"
	@echo "\n🔍 3. Type checking mypy..."
	mypy scraper/ core/ tools/ --ignore-missing-imports || (echo "⚠️  Type checking warnings" && true)
	@echo "\n🧪 4. Tests avec coverage..."
	pytest --cov --cov-report=term-missing || (echo "❌ Tests échoués" && exit 1)
	@echo "\n✅ Tous les checks sont OK ! 🎉"
