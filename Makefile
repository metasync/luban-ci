# Luban CI Makefile

# Load Configuration
include Makefile.env
export

# Load all .env files in secrets directory
ENV_FILES := $(wildcard secrets/*.env)
ifneq (,$(ENV_FILES))
    include $(ENV_FILES)
    export
endif

.PHONY: all help \
        secrets \
        stack-build stack-push \
        builder-build builder-push \
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
	@echo "Creating namespace $(K8S_NAMESPACE)..."
	@kubectl create ns $(K8S_NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@echo "Creating Quay secrets..."
	@kubectl delete secret quay-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret docker-registry quay-creds \
		-n $(K8S_NAMESPACE) \
		--docker-server=$(REGISTRY_SERVER) \
		--docker-username="$(QUAY_USERNAME)" \
		--docker-password="$(QUAY_PASSWORD)" \
		--docker-email="$(REGISTRY_EMAIL)"
	@echo "Creating Harbor secrets..."
	@kubectl delete secret harbor-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret docker-registry harbor-creds \
		-n $(K8S_NAMESPACE) \
		--docker-server=$(HARBOR_SERVER) \
		--docker-username='$(HARBOR_USERNAME)' \
		--docker-password='$(HARBOR_PASSWORD)' \
		--docker-email="$(REGISTRY_EMAIL)"
	@echo "Creating Harbor Read-Only secrets..."
	@kubectl delete secret harbor-ro-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret docker-registry harbor-ro-creds \
		-n $(K8S_NAMESPACE) \
		--docker-server=$(HARBOR_SERVER) \
		--docker-username='$(HARBOR_RO_USERNAME)' \
		--docker-password='$(HARBOR_RO_PASSWORD)' \
		--docker-email="$(REGISTRY_EMAIL)"
	@echo "Creating Harbor API secrets..."
	@kubectl delete secret harbor-api-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret generic harbor-api-creds \
		-n $(K8S_NAMESPACE) \
		--from-literal=HARBOR_SERVER=$(HARBOR_SERVER) \
		--from-literal=HARBOR_USERNAME='$(HARBOR_USERNAME)' \
		--from-literal=HARBOR_PASSWORD='$(HARBOR_PASSWORD)'
	@echo "Creating GitHub secrets..."
	@kubectl delete secret github-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret generic github-creds \
		-n $(K8S_NAMESPACE) \
		--from-literal=username="$(GITHUB_USERNAME)" \
		--from-literal=token="$(GITHUB_TOKEN)"
	@echo "Creating Cloudflare API secrets..."
	@kubectl create secret generic cloudflare-api-token \
		-n cert-manager \
		--from-literal=api-token='$(CLOUDFLARE_API_TOKEN)' \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "Secrets setup complete."

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

tools-image-build: ## Build gitops-utils tooling image
	@$(MAKE) -C tools/gitops-utils build
	@$(MAKE) -C tools/gitops-provisioner build
	@$(MAKE) -C tools/gitsrc-provisioner build

tools-image-push: ## Push gitops-utils tooling image (build if missing)
	@$(MAKE) -C tools/gitops-utils push
	@$(MAKE) -C tools/gitops-provisioner push
	@$(MAKE) -C tools/gitsrc-provisioner push

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

venv-clean: ## Cleanup virtual environment
	@echo "Removing virtual environment..."
	@rm -rf .venv

docker-image-prune: ## Prune local Docker images
	@echo "Pruning local Docker images..."
	@docker image prune -f

clean: pipeline-clean venv-clean docker-image-prune ## Cleanup local artifacts
