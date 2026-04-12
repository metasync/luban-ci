# Luban Provisioner Tooling Makefile

include Makefile.env
export

.PHONY: build push list-templates render-template clean-rendered lint format help

help: ## Show this help message
	@echo "Available targets:"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build luban provisioner tooling image
	@docker build --platform linux/amd64 \
		-t $(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/luban-provisioner:$(LUBAN_PROVISIONER_VERSION) .

push: ## Push luban-provisioner tooling image (build if missing)
	@IMAGE=$(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/luban-provisioner:$(LUBAN_PROVISIONER_VERSION); \
	if [ "$(FORCE_PUSH)" = "1" ]; then \
		echo "FORCE_PUSH=1 set. Building and pushing $$IMAGE..."; \
		$(MAKE) build || exit 1; \
		if [ -n "$(QUAY_USERNAME)" ] && [ -n "$(QUAY_PASSWORD)" ]; then \
			echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin $(REGISTRY_SERVER) || exit 1; \
		else \
			echo "QUAY_USERNAME/QUAY_PASSWORD not set; relying on existing docker credentials"; \
		fi; \
		docker push $$IMAGE || exit 1; \
		exit 0; \
	fi; \
	if docker manifest inspect $$IMAGE > /dev/null 2>&1; then \
		echo "Tooling image $$IMAGE already exists. Skipping build & push."; \
	else \
		echo "Tooling image $$IMAGE not found. Building and pushing..."; \
		$(MAKE) build || exit 1; \
		if [ -n "$(QUAY_USERNAME)" ] && [ -n "$(QUAY_PASSWORD)" ]; then \
			echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin $(REGISTRY_SERVER) || exit 1; \
		else \
			echo "QUAY_USERNAME/QUAY_PASSWORD not set; relying on existing docker credentials"; \
		fi; \
		docker push $$IMAGE || exit 1; \
	fi

list-templates: ## List available project templates
	@ls -1 $(TEMPLATES_DIR)

render-template: ## Render a template (e.g., make render-template T=luban-python-template)
	@T=$(T); \
	TEMPLATE=$${T:-$(DEFAULT_TEMPLATE)}; \
	echo "Rendering template: $$TEMPLATE to $(OUTPUT_DIR)..."; \
	mkdir -p $(OUTPUT_DIR); \
	PYTHONWARNINGS="ignore" uv run cookiecutter --no-input -f -o $(OUTPUT_DIR) $(TEMPLATES_DIR)/$$TEMPLATE \
		project_name="Test Project" \
		app_name="test_app" \
		package_name="test_app" \
		dagster_version="1.12.19" \
		author_name="Luban Team" \
		author_email="luban@example.com" || exit 1; \
	echo "Done. Rendered project is at $(OUTPUT_DIR)/test_app"

clean-rendered: ## Remove all rendered templates
	@echo "Cleaning $(OUTPUT_DIR)..."
	@rm -rf $(OUTPUT_DIR)

lint: ## Run python lint checks (ruff)
	@TMPDIR=/tmp uv run --group dev ruff check src/luban_provisioner tests

format: ## Auto-fix lint and format python (ruff)
	@TMPDIR=/tmp uv run --group dev ruff check --fix src/luban_provisioner tests
	@TMPDIR=/tmp uv run --group dev ruff format src/luban_provisioner tests
