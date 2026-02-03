# Builder Makefile

include Makefile.env
export

.PHONY: build push

build: ## Create the CNB Builder
	@echo "Downloading Lifecycle for $(PLATFORM)..."
	@mkdir -p cache
	@curl -L -o cache/lifecycle.tgz $(LIFECYCLE_URI)
	@echo "Creating Builder for $(PLATFORM)..."
	@pack builder create $(BUILDER_IMAGE) --config builder.toml $(PACK_FLAGS) --tag $(REMOTE_BUILDER_TAG_IMMUTABLE)
	@echo "Builder created."

push: ## Check remote, build (if needed), tag and push Builder Image
	$(MAKE) build || exit 1; \
	if [ "$(PLATFORM)" = "$(LOCAL_PLATFORM)" ]; then \
		echo "Logging in to Quay.io..."; \
		echo "$(QUAY_PASSWORD)" | docker login -u "$(QUAY_USERNAME)" --password-stdin $(REGISTRY_SERVER); \
		echo "Tagging builder as $(REMOTE_BUILDER_TAG_IMMUTABLE)..."; \
		docker tag $(BUILDER_IMAGE) $(REMOTE_BUILDER_TAG_IMMUTABLE); \
		echo "Pushing images..."; \
		docker push $(BUILDER_IMAGE); \
		docker push $(REMOTE_BUILDER_TAG_IMMUTABLE); \
	else \
		echo "Builder pushed directly via pack --publish"; \
	fi
