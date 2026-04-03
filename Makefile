# Luban CI Makefile

# Load Configuration
include Makefile.env
export

.PHONY: all help \
        secrets \
        secrets-dry-run \
        stack-build stack-push \
        builder-build builder-push \
        update-default-git-provider \
        pipeline-deploy pipeline-clean pipeline-logs \
        events-deploy events-webhook-secret \
        test-ci-pipeline test-events-webhook test-events-webhook-py \
        tunnel-setup \
        clean

help: ## Show this help message
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

all: secrets \
    stack-push \
    buildpack-package \
    builder-push \
    tools-image-push \
    pipeline-deploy \
    events-deploy \
    events-webhook-secret ## Setup secrets, push images, deploy pipeline and events

# --- Secrets Management ---

secrets: ## Create/Update Kubernetes secrets from env files
	@$(MAKE) -C manifests secrets

secrets-dry-run: ## Validate secret templates render (does not write to cluster)
	@$(MAKE) -C manifests secrets-dry-run

# --- Buildpack Management ---

buildpack-package: ## Package and publish the custom buildpack to Quay.io
	@echo "Packaging Buildpack..."
	@cd buildpacks/python-uv && pack buildpack package $(BUILDPACK_IMAGE) --config package.toml --publish --target $(PLATFORM)
	@echo "Buildpack published: $(BUILDPACK_IMAGE)"

# --- Stack Management ---

stack-build: ## Build the stack images (base, run, build)
	@$(MAKE) -C stack build

stack-push: ## Check remote, build (if needed), tag and push Stack Images (Run & Build)
	@$(MAKE) -C stack push

# --- Builder Management ---

builder-build: ## Create the CNB Builder
	@$(MAKE) -C builder build

builder-push: ## Check remote, build (if needed), tag and push Builder Image
	@$(MAKE) -C builder push

update-default-git-provider: ## Update workflow git_provider defaults from luban-config
	@python3 scripts/update-default-git-provider.py

tools-image-build: ## Build gitops-utils tooling image
	@$(MAKE) -C tools/gitops-utils build
	@$(MAKE) -C tools/luban-provisioner build

tools-image-push: ## Push gitops-utils tooling image (build if missing)
	@$(MAKE) -C tools/gitops-utils push
	@$(MAKE) -C tools/luban-provisioner push

# --- Pipeline Management ---

pipeline-deploy: ## Deploy Argo Workflow Template and RBAC
	@$(MAKE) -C manifests deploy

pipeline-clean: ## Delete all workflows
	@echo "Cleaning up workflows..."
	@$(MAKE) -C manifests clean

pipeline-logs: ## Show logs for the latest kpack build of the app. Usage: make pipeline-logs APP_NAME=my-app
	@$(MAKE) -C manifests logs

# --- Events Management ---

events-deploy: ## Deploy Argo Events (EventBus, EventSource, Sensor)
	@$(MAKE) -C events deploy

events-webhook-secret: ## Ensure GitHub webhook secret exists (skip if present)
	@$(MAKE) -C events webhook-secret

events-webhook-secret-rotate: ## Force generate and rotate GitHub webhook secret
	@$(MAKE) -C events webhook-secret-rotate

# --- Development & Testing ---

test-ci-pipeline: test-ci-pipeline-kpack ## Trigger the kpack CI Workflow (default)

test-ci-pipeline-kpack: ## Trigger the kpack CI Workflow
	@$(MAKE) -C test test-ci-pipeline

test-events-webhook: ## Send signed push payload via gateway to trigger Workflow
	@$(MAKE) -C test test-webhook

test-events-webhook-py: ## Send signed push payload via gateway to trigger Workflow (Python)
	@$(MAKE) -C test test-webhook-py

tunnel-setup: ## Setup Cloudflare Tunnel for webhook exposure (optional)
	@$(MAKE) -C manifests tunnel-setup

patch-coredns: ## Patch CoreDNS to support internal DNS resolution for local testing
	@./tools/patch-coredns.sh

venv-clean: ## Cleanup virtual environment
	@echo "Removing virtual environment..."
	@rm -rf .venv

docker-image-prune: ## Prune local Docker images
	@echo "Pruning local Docker images..."
	@docker image prune -f

clean: pipeline-clean venv-clean docker-image-prune ## Cleanup local artifacts
