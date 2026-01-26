# GitOps CLI Tooling Makefile

include Makefile.env
export

.PHONY: build push

build: ## Build gitops utils tooling image
	@docker build --platform linux/amd64 \
		--build-arg ARGO_VERSION=$(ARGO_CLI_VERSION) \
		-t $(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/gitops-utils:$(GITOPS_UTILS_VERSION) .

push: ## Push gitops-utils tooling image (build if missing)
	@IMAGE=$(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/gitops-utils:$(GITOPS_UTILS_VERSION); \
	if docker manifest inspect $$IMAGE > /dev/null 2>&1; then \
		echo "Tooling image $$IMAGE already exists. Skipping build & push."; \
	else \
		echo "Tooling image $$IMAGE not found. Building and pushing..."; \
		$(MAKE) build || exit 1; \
		echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin $(REGISTRY_SERVER); \
		docker push $$IMAGE; \
	fi
