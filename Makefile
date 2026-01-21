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
        pipeline-deploy pipeline-run pipeline-clean \
        clean test

help: ## Show this help message
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

all: secrets \
    stack-push \
    builder-push \
    pipeline-deploy ## Setup secrets, push images (if needed), and deploy pipeline

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
	@echo "Creating GitHub secrets..."
	@kubectl delete secret github-creds -n $(K8S_NAMESPACE) --ignore-not-found
	@kubectl create secret generic github-creds \
		-n $(K8S_NAMESPACE) \
		--from-literal=username="$(GITHUB_USERNAME)" \
		--from-literal=token="$(GITHUB_TOKEN)"
	@echo "Secrets setup complete."

# --- Stack Management ---

stack-build: ## Build the stack images (base, run, build)
	@echo "Building Stack Images for $(PLATFORM)..."
	@cd stack && docker build --platform $(PLATFORM) -t $(BASE_IMAGE) base
	@cd stack && docker build --platform $(PLATFORM) -t $(RUN_IMAGE) run
	@cd stack && docker build --platform $(PLATFORM) -t $(BUILD_IMAGE) build
	@echo "Stack build complete."


stack-push: ## Check remote, build (if needed), tag and push Stack Images (Run & Build)
	@echo "--- Handling Run Image ---"
	@echo "Checking if $(REMOTE_RUN_TAG_IMMUTABLE) exists..."
	@if docker manifest inspect $(REMOTE_RUN_TAG_IMMUTABLE) > /dev/null 2>&1; then \
		echo "Image $(REMOTE_RUN_TAG_IMMUTABLE) already exists. Skipping build and push."; \
	else \
		echo "Image not found. Building..."; \
		$(MAKE) stack-build || exit 1; \
		echo "Tagging run image as $(REMOTE_RUN_TAG_IMMUTABLE)..."; \
		docker tag $(RUN_IMAGE) $(REMOTE_RUN_TAG_IMMUTABLE); \
		docker push $(RUN_IMAGE); \
		docker push $(REMOTE_RUN_TAG_IMMUTABLE); \
	fi
	@echo "--- Handling Build Image ---"
	@echo "Checking if $(REMOTE_BUILD_TAG_IMMUTABLE) exists..."
	@if docker manifest inspect $(REMOTE_BUILD_TAG_IMMUTABLE) > /dev/null 2>&1; then \
		echo "Image $(REMOTE_BUILD_TAG_IMMUTABLE) already exists. Skipping build and push."; \
	else \
		echo "Image not found. Building..."; \
		$(MAKE) stack-build || exit 1; \
		echo "Tagging build image as $(REMOTE_BUILD_TAG_IMMUTABLE)..."; \
		docker tag $(BUILD_IMAGE) $(REMOTE_BUILD_TAG_IMMUTABLE); \
		echo "Pushing build images..."; \
		docker push $(BUILD_IMAGE); \
		docker push $(REMOTE_BUILD_TAG_IMMUTABLE); \
	fi

# --- Builder Management ---

builder-build: ## Create the CNB Builder
	@echo "Downloading Lifecycle for $(PLATFORM)..."
	@mkdir -p cache
	@curl -L -o cache/lifecycle.tgz $(LIFECYCLE_URI)
	@echo "Creating Builder for $(PLATFORM)..."
	@pack builder create $(BUILDER_IMAGE) --config builder.toml $(PACK_FLAGS) --tag $(REMOTE_BUILDER_TAG_IMMUTABLE)
	@echo "Builder created."

builder-push: ## Check remote, build (if needed), tag and push Builder Image
	@echo "Checking if $(REMOTE_BUILDER_TAG_IMMUTABLE) exists..."
	@if docker manifest inspect $(REMOTE_BUILDER_TAG_IMMUTABLE) > /dev/null 2>&1; then \
		echo "Image $(REMOTE_BUILDER_TAG_IMMUTABLE) already exists. Skipping build and push."; \
	else \
		echo "Image not found. Building..."; \
		$(MAKE) builder-build || exit 1; \
		if [ "$(PLATFORM)" = "$(LOCAL_PLATFORM)" ]; then \
			echo "Logging in to Quay.io..."; \
			echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin quay.io; \
			echo "Tagging builder as $(REMOTE_BUILDER_TAG_IMMUTABLE)..."; \
			docker tag $(BUILDER_IMAGE) $(REMOTE_BUILDER_TAG_IMMUTABLE); \
			echo "Pushing images..."; \
			docker push $(BUILDER_IMAGE); \
			docker push $(REMOTE_BUILDER_TAG_IMMUTABLE); \
		else \
			echo "Builder pushed directly via pack --publish"; \
		fi \
	fi

# --- Pipeline Management ---

pipeline-deploy: ## Deploy Argo Workflow Manifests
	@echo "Deploying Pipeline Manifests..."
	@kubectl apply -f manifests/pipeline-sa.yaml
	@kubectl apply -f manifests/ci-dind-workflow-template.yaml
	@echo "Pipeline deployed."

pipeline-run: ## Trigger the CI Workflow
	@echo "Triggering CI Workflow..."
	@kubectl delete wf --all -n $(K8S_NAMESPACE)
	@kubectl create -f manifests/ci-dind-workflow.yaml
	@echo "Workflow started. Watch status with: kubectl get wf -n $(K8S_NAMESPACE) -w"

pipeline-clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)

# --- Development & Testing ---

test: ## Run local test of the sample app
	@echo "Testing Sample App..."
	@docker pull $(REGISTRY_SERVER)/$(QUAY_NAMESPACE)/sample-app:$(TAG_PREFIX)
	@docker rm -f sample-app-test || true
	@docker run -d -p 8080:8080 --name sample-app-test $(REGISTRY_SERVER)/$(QUAY_NAMESPACE)/sample-app:$(TAG_PREFIX)
	@sleep 2
	@curl -v http://localhost:8080/
	@echo "Test passed."
	@docker rm -f sample-app-test

clean: pipeline-clean ## Cleanup local artifacts
	@echo "Cleaning up..."
	@rm -rf .venv
	@docker rmi $(BUILDER_IMAGE) $(RUN_IMAGE) $(REMOTE_BUILDER_TAG) $(REMOTE_RUN_TAG) || true

prune: ## Prune local Docker images
	@echo "Pruning local Docker images..."
	@docker image prune -f
