# GitOps Provisioner Tooling Makefile

include Makefile.env
export

.PHONY: build push

build: ## Build gitops provisioner tooling image
	@docker build --platform linux/amd64 \
		-t $(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/gitops-provisioner:$(GITOPS_PROVISIONER_VERSION) .

push: ## Push gitops-provisioner tooling image (build if missing)
	@IMAGE=$(REGISTRY_SERVER)/$(REGISTRY_NAMESPACE)/gitops-provisioner:$(GITOPS_PROVISIONER_VERSION); \
	if docker manifest inspect $$IMAGE > /dev/null 2>&1; then \
		echo "Tooling image $$IMAGE already exists. Skipping build & push."; \
	else \
		echo "Tooling image $$IMAGE not found. Building and pushing..."; \
		$(MAKE) build || exit 1; \
		echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin $(REGISTRY_SERVER); \
		docker push $$IMAGE; \
	fi
