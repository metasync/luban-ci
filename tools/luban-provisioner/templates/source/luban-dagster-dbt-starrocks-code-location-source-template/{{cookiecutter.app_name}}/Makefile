
.PHONY: help setup install dev test check-db dbt-deps dbt-build dbt-run clean


# Load local environment variables (if present) for dbt/Dagster commands.
# The leading '-' keeps make from erroring before `.env` exists.
-include .env
export

DBT_VARS ?=

help: ## Show available targets
	@echo "Available targets:"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: install ## Setup local development environment
	@echo "Setting up local development environment..."
	@if [ ! -f .env ]; then \
		echo "Copying .env.example to .env..."; \
		cp .env.example .env; \
		echo "Please update .env with your local database credentials."; \
	else \
		echo ".env file already exists. Skipping."; \
	fi
	@echo "Setup complete!"


install: ## Install or update python dependencies
	@echo "Installing dependencies..."
	uv sync


dev: ## Run Dagster webserver for local development
	uv run dagster dev


test: ## Run unit tests and dbt tests
	@echo "Running python unit tests..."
	uv run pytest tests/
	@echo "Running dbt tests..."
	@if [ -z "$(DBT_VARS)" ]; then \
		echo "DBT_VARS is required for dbt execution (partition window vars). Example:"; \
		echo "  export DBT_VARS='{\"min_date\":\"2026-01-02\",\"max_date\":\"2026-01-03\",\"min_datetime\":\"2026-01-02 00:00:00\",\"max_datetime\":\"2026-01-03 00:00:00\"}'"; \
		exit 1; \
	fi
	uv run dbt test --project-dir $(DBT_PROJECT_DIR) --vars '$(DBT_VARS)'


check-db: ## Test connectivity to the StarRocks database
	@echo "Testing StarRocks connectivity using dbt debug..."
	uv run dbt debug --project-dir $(DBT_PROJECT_DIR)


dbt-deps: ## Install dbt dependencies
	uv run dbt deps --project-dir $(DBT_PROJECT_DIR)


dbt-build: ## Build the dbt project (run + test)
	@if [ -z "$(DBT_VARS)" ]; then \
		echo "DBT_VARS is required for dbt execution (partition window vars). Example:"; \
		echo "  export DBT_VARS='{\"min_date\":\"2026-01-02\",\"max_date\":\"2026-01-03\",\"min_datetime\":\"2026-01-02 00:00:00\",\"max_datetime\":\"2026-01-03 00:00:00\"}'"; \
		exit 1; \
	fi
	uv run dbt build --project-dir $(DBT_PROJECT_DIR) --vars '$(DBT_VARS)'


dbt-run: ## Run the dbt project (without testing)
	@if [ -z "$(DBT_VARS)" ]; then \
		echo "DBT_VARS is required for dbt execution (partition window vars). Example:"; \
		echo "  export DBT_VARS='{\"min_date\":\"2026-01-02\",\"max_date\":\"2026-01-03\",\"min_datetime\":\"2026-01-02 00:00:00\",\"max_datetime\":\"2026-01-03 00:00:00\"}'"; \
		exit 1; \
	fi
	uv run dbt run --project-dir $(DBT_PROJECT_DIR) --vars '$(DBT_VARS)'


clean: ## Clean up temporary generated files and virtual environment
	@echo "Cleaning up generated files..."
	rm -rf .venv
	rm -rf $(DBT_PROJECT_DIR)/target
	rm -rf $(DBT_PROJECT_DIR)/dbt_packages
	rm -rf $(DBT_PROJECT_DIR)/logs
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	@echo "Clean complete!"
