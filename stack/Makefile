# Stack Images Makefile

include Makefile.env
export

.PHONY: build push

build: ## Build the stack images (base, run, build)
	@echo "Building Stack Images for $(PLATFORM)..."
	@docker build --platform $(PLATFORM) -t $(BASE_IMAGE) base
	@docker build --platform $(PLATFORM) -t $(RUN_IMAGE) run
	@docker build --platform $(PLATFORM) -t $(BUILD_IMAGE) build
	@echo "Stack build complete."

push: ## Check remote, build (if needed), tag and push Stack Images (Run & Build)
	@echo "--- Handling Run Image ---"
	@echo "Checking if $(REMOTE_RUN_TAG_IMMUTABLE) exists..."
	@if docker manifest inspect $(REMOTE_RUN_TAG_IMMUTABLE) > /dev/null 2>&1; then \
		echo "Image $(REMOTE_RUN_TAG_IMMUTABLE) already exists. Skipping build and push."; \
	else \
		echo "Image not found. Building..."; \
		$(MAKE) build || exit 1; \
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
		$(MAKE) build || exit 1; \
		echo "Tagging build image as $(REMOTE_BUILD_TAG_IMMUTABLE)..."; \
		docker tag $(BUILD_IMAGE) $(REMOTE_BUILD_TAG_IMMUTABLE); \
		echo "Pushing build images..."; \
		docker push $(BUILD_IMAGE); \
		docker push $(REMOTE_BUILD_TAG_IMMUTABLE); \
	fi
