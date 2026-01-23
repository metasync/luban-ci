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
    buildpack-package \
    builder-push \
    pipeline-deploy \
    events-deploy ## Setup secrets, push images, deploy pipeline and events

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

# --- Buildpack Management ---

buildpack-package: ## Package and publish the custom buildpack to Quay.io
	@echo "Packaging Buildpack..."
	@cd buildpacks/python-uv && pack buildpack package $(BUILDPACK_IMAGE) --config package.toml --publish --target $(PLATFORM)
	@echo "Buildpack published: $(BUILDPACK_IMAGE)"

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

pipeline-deploy: ## Deploy Argo Workflow Template and RBAC
	@echo "Deploying Workflow RBAC..."
	@kubectl apply -f manifests/pipeline-sa.yaml
	@echo "Deploying kpack Stack and Builder..."
	@kubectl apply -f manifests/kpack-stack.yaml
	@kubectl apply -f manifests/kpack-builder.yaml
	@echo "Deploying Workflow Templates..."
	@kubectl apply -f manifests/ci-dind-workflow-template.yaml
	@kubectl apply -f manifests/ci-kpack-workflow-template.yaml
	@echo "Pipeline deployed."

pipeline-run: pipeline-run-kpack ## Trigger the kpack CI Workflow (default)

pipeline-run-dind: ## Trigger the DinD CI Workflow
	@echo "Triggering DinD CI Workflow..."
	@kubectl delete wf --all -n $(K8S_NAMESPACE)
	@kubectl create -f manifests/ci-dind-workflow.yaml
	@echo "Workflow started. Watch status with: kubectl get wf -n $(K8S_NAMESPACE) -w"

pipeline-run-kpack: ## Trigger the kpack CI Workflow
	@echo "Triggering kpack CI Workflow..."
	@kubectl delete wf --all -n $(K8S_NAMESPACE)
	@kubectl create -f manifests/ci-kpack-workflow.yaml
	@echo "Workflow started. Watch status with: kubectl get wf -n $(K8S_NAMESPACE) -w"

pipeline-logs: ## Show logs for the latest kpack build of the app
	@echo "Fetching logs for $(APP_NAME) in $(K8S_NAMESPACE)..."
	@kp build logs $(APP_NAME) -n $(K8S_NAMESPACE)

pipeline-clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)

# --- Development & Testing ---

test: ## Run local test of the sample app
	@echo "Testing Sample App..."
	@docker pull $(REGISTRY_SERVER)/$(QUAY_NAMESPACE)/$(APP_NAME):$(APP_REVISION)
	@docker rm -f $(APP_NAME)-test >/dev/null 2>&1 || true
	@docker run -d -p 8080:8080 --name $(APP_NAME)-test $(REGISTRY_SERVER)/$(QUAY_NAMESPACE)/$(APP_NAME):$(APP_REVISION)
	@echo "Waiting for application to start..."
	@for i in 1 2 3 4 5; do \
		if curl -s http://127.0.0.1:8080/ >/dev/null; then \
			break; \
		fi; \
		echo "Retrying in 2 seconds..."; \
		sleep 2; \
	done
	@curl -v http://127.0.0.1:8080/
	@echo "Test passed."
	@docker rm -f $(APP_NAME)-test >/dev/null 2>&1

clean: pipeline-clean ## Cleanup local artifacts
	@echo "Cleaning up..."
	@rm -rf .venv
	@docker rmi $(BUILDER_IMAGE) $(RUN_IMAGE) $(REMOTE_BUILDER_TAG) $(REMOTE_RUN_TAG) || true

prune: ## Prune local Docker images
	@echo "Pruning local Docker images..."
	@docker image prune -f

# --- Events Management ---

events-deploy: ## Deploy Argo Events (EventBus, EventSource, Sensor)
	@echo "Deploying Argo Events..."
	@kubectl apply -f events/eventbus.yaml
	@kubectl apply -f events/event-source.yaml
	@kubectl apply -f events/sensor.yaml
	@kubectl apply -f events/gateway.yaml
	@echo "Argo Events deployed."

events-webhook-secret: ## Generate and create GitHub webhook secret in K8s
	@echo "Generating webhook secret for namespace $(K8S_NAMESPACE)..."
	@SECRET=$$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32); \
	kubectl delete secret github-webhook-secret -n $(K8S_NAMESPACE) --ignore-not-found; \
	kubectl create secret generic github-webhook-secret -n $(K8S_NAMESPACE) --from-literal=secret="$$SECRET"; \
	echo "Webhook secret created in K8s. Use this exact value in GitHub webhook settings:"; \
	echo "$$SECRET"

events-webhook-create-repo: ## Create a repo webhook via GitHub API (requires GITHUB_TOKEN)
	@echo "Creating GitHub repo webhook..."
	@GITHUB_OWNER=$${GITHUB_OWNER:-metasync}; \
	GITHUB_REPO=$${GITHUB_REPO:-luban-hello-world-py}; \
	WEBHOOK_URL=$${WEBHOOK_URL:-https://webhook.luban.k8s.orb.local/push}; \
	SECRET=$$(kubectl get secret github-webhook-secret -n $(K8S_NAMESPACE) -o jsonpath='{.data.secret}' | base64 --decode); \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required"; exit 1; fi; \
	BODY=$$(printf '{"name":"web","active":true,"events":["push"],"config":{"url":"%s","content_type":"json","secret":"%s","insecure_ssl":"0"}}' "$$WEBHOOK_URL" "$$SECRET"); \
	curl -s -X POST \
		-H "Authorization: Bearer $$GITHUB_TOKEN" \
		-H "Accept: application/vnd.github+json" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/repos/$$GITHUB_OWNER/$$GITHUB_REPO/hooks \
		-d "$$BODY"

events-webhook-create-org: ## Create an org webhook via GitHub API (requires admin:org_hook)
	@echo "Creating GitHub organization webhook..."
	@GITHUB_ORG=$${GITHUB_ORG:-metasync}; \
	WEBHOOK_URL=$${WEBHOOK_URL:-https://webhook.luban.k8s.orb.local/push}; \
	SECRET=$$(kubectl get secret github-webhook-secret -n $(K8S_NAMESPACE) -o jsonpath='{.data.secret}' | base64 --decode); \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required and must have admin:org_hook scope"; exit 1; fi; \
	BODY=$$(printf '{"name":"web","active":true,"events":["push"],"config":{"url":"%s","content_type":"json","secret":"%s","insecure_ssl":"0"}}' "$$WEBHOOK_URL" "$$SECRET"); \
	curl -s -X POST \
		-H "Authorization: Bearer $$GITHUB_TOKEN" \
		-H "Accept: application/vnd.github+json" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/orgs/$$GITHUB_ORG/hooks \
		-d "$$BODY"

events-webhook-test: ## Send signed push payload via gateway to trigger Workflow
	@echo "Testing signed webhook delivery via gateway..."
	@GATEWAY_HOSTNAME=$${GATEWAY_HOSTNAME:-webhook.luban.k8s.orb.local}; \
	GATEWAY_HOST=$${GATEWAY_HOST:-127.0.0.1}; \
	GATEWAY_PORT=$${GATEWAY_PORT:-8443}; \
	REPO_URL=$${REPO_URL:-https://github.com/metasync/luban-hello-world-py.git}; \
	REVISION=$${REVISION:-main}; \
	APP_NAME=$${APP_NAME:-luban-hello-world-py}; \
	SECRET=$$(kubectl get secret github-webhook-secret -n $(K8S_NAMESPACE) -o jsonpath='{.data.secret}' | base64 --decode); \
	BODY=$$(printf '{"ref":"refs/heads/%s","after":"%s","repository":{"clone_url":"%s","name":"%s"}}' "$$REVISION" "$$REVISION" "$$REPO_URL" "$$APP_NAME"); \
	SIG=$$(printf '%s' "$$BODY" | openssl dgst -sha256 -hmac "$$SECRET" | sed -E 's/^.*= //'); \
	curl -v -k --resolve "$$GATEWAY_HOSTNAME:$$GATEWAY_PORT:$$GATEWAY_HOST" \
		-H "Content-Type: application/json" \
		-H "X-Hub-Signature-256: sha256=$$SIG" \
		-d "$$BODY" \
		https://$$GATEWAY_HOSTNAME:$$GATEWAY_PORT/push; \
	echo "Latest workflow:"; \
	kubectl get wf -n $(K8S_NAMESPACE) --sort-by=.metadata.creationTimestamp | tail -n 1

gitops-repo-create: ## Create GitOps repo (defaults: org=metasync, name=luban-gitops)
	@echo "Creating GitOps repository..."
	@GITHUB_ORG=$${GITHUB_ORG:-metasync}; \
	GITOPS_REPO_NAME=$${GITOPS_REPO_NAME:-luban-gitops}; \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required"; exit 1; fi; \
	BODY=$$(printf '{"name":"%s","private":false,"auto_init":true}' "$$GITOPS_REPO_NAME"); \
	curl -s -X POST \
		-H "Authorization: Bearer $$GITHUB_TOKEN" \
		-H "Accept: application/vnd.github+json" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/orgs/$$GITHUB_ORG/repos \
		-d "$$BODY"

gitops-repo-create-user: ## Create per-app GitOps repo under the authenticated user
	@echo "Creating GitOps repository under user account..."
	@GITOPS_REPO_NAME=$${GITOPS_REPO_NAME:-luban-hello-world-py-gitops}; \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required"; exit 1; fi; \
	BODY=$$(printf '{"name":"%s","private":false,"auto_init":false}' "$$GITOPS_REPO_NAME"); \
	curl -s -X POST \
		-H "Authorization: Bearer $$GITHUB_TOKEN" \
		-H "Accept: application/vnd.github+json" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/user/repos \
		-d "$$BODY"

gitops-repo-push: ## Push argocd and app (kustomize) to per-app GitOps repo
	@echo "Pushing GitOps content..."
	@GITHUB_OWNER=$${GITHUB_OWNER:-metasync}; \
	GITOPS_REPO_NAME=$${GITOPS_REPO_NAME:-luban-hello-world-py-gitops}; \
	GITOPS_REPO_URL=$${GITOPS_REPO_URL:-https://github.com/$$GITHUB_OWNER/$$GITOPS_REPO_NAME.git}; \
	TMP_DIR=$$(mktemp -d); \
	git clone $$GITOPS_REPO_URL $$TMP_DIR/repo; \
	# Clean any non-kustomize root files
	rm -f $$TMP_DIR/repo/app/deployment.yaml $$TMP_DIR/repo/app/kustomization.yaml || true; \
	rm -f $$TMP_DIR/repo/argocd/application.yaml $$TMP_DIR/repo/argocd/kustomization.yaml || true; \
	mkdir -p $$TMP_DIR/repo/app/base; \
	echo "Generating minimal deployment and service manifests in app/base"; \
	cat > $$TMP_DIR/repo/app/base/deployment.yaml <<'EOF'\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: luban-hello-world-py\n  namespace: luban-ci\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: luban-hello-world-py\n  template:\n    metadata:\n      labels:\n        app: luban-hello-world-py\n    spec:\n      containers:\n      - name: app\n        image: quay.io/luban-ci/luban-hello-world-py:main\n        ports:\n        - containerPort: 8080\nEOF\n; \
	cat > $$TMP_DIR/repo/app/base/service.yaml <<'EOF'\napiVersion: v1\nkind: Service\nmetadata:\n  name: luban-hello-world-py\n  namespace: luban-ci\nspec:\n  type: ClusterIP\n  selector:\n    app: luban-hello-world-py\n  ports:\n  - name: http\n    port: 8080\n    targetPort: 8080\nEOF\n; \
	printf "resources:\n  - deployment.yaml\n  - service.yaml\n" > $$TMP_DIR/repo/app/base/kustomization.yaml; \
	mkdir -p $$TMP_DIR/repo/app/overlays/snd $$TMP_DIR/repo/app/overlays/prd; \
	printf "resources:\n  - ../../base\n" > $$TMP_DIR/repo/app/overlays/snd/kustomization.yaml; \
	printf "resources:\n  - ../../base\n" > $$TMP_DIR/repo/app/overlays/prd/kustomization.yaml; \
	mkdir -p $$TMP_DIR/repo/argocd/base $$TMP_DIR/repo/argocd/overlays/snd $$TMP_DIR/repo/argocd/overlays/prd; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py\n  namespace: argocd\nspec:\n  project: default\n  source:\n    repoURL: %s\n    targetRevision: main\n    path: app/base\n  destination:\n    server: https://kubernetes.default.svc\n    namespace: luban-ci\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n    - CreateNamespace=true\n" "$$GITOPS_REPO_URL" > $$TMP_DIR/repo/argocd/base/application.yaml; \
	printf "resources:\n  - application.yaml\n" > $$TMP_DIR/repo/argocd/base/kustomization.yaml; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py\n  namespace: argocd\nspec:\n  project: devops-snd\n  source:\n    path: app/overlays/snd\n" > $$TMP_DIR/repo/argocd/overlays/snd/application-patch.yaml; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py-snd\n  namespace: argocd\nspec:\n  project: devops-snd\n  source:\n    repoURL: %s\n    targetRevision: main\n    path: app/overlays/snd\n  destination:\n    server: https://kubernetes.default.svc\n    namespace: luban-ci\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n    - CreateNamespace=true\n" "$$GITOPS_REPO_URL" > $$TMP_DIR/repo/argocd/overlays/snd/application-snd.yaml; \
	printf "resources:\n  - application-snd.yaml\n" > $$TMP_DIR/repo/argocd/overlays/snd/kustomization.yaml; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py\n  namespace: argocd\nspec:\n  project: devops-prd\n  source:\n    path: app/overlays/prd\n" > $$TMP_DIR/repo/argocd/overlays/prd/application-patch.yaml; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py-prd\n  namespace: argocd\nspec:\n  project: devops-prd\n  source:\n    repoURL: %s\n    targetRevision: main\n    path: app/overlays/prd\n  destination:\n    server: https://kubernetes.default.svc\n    namespace: luban-ci\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n    - CreateNamespace=true\n" "$$GITOPS_REPO_URL" > $$TMP_DIR/repo/argocd/overlays/prd/application-prd.yaml; \
	printf "resources:\n  - application-prd.yaml\n" > $$TMP_DIR/repo/argocd/overlays/prd/kustomization.yaml; \
	cd $$TMP_DIR/repo; \
	git config user.name "Luban CI"; \
	git config user.email "ci@luban.com"; \
	git add .; \
	git commit -m "Update GitOps content (app base/overlays, argocd overlays)"; \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required"; exit 1; fi; \
	GIT_ASKPASS=$$(mktemp); \
	printf '#!/bin/sh\necho $$GITHUB_TOKEN\n' > $$GIT_ASKPASS; \
	chmod +x $$GIT_ASKPASS; \
	GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=$$GIT_ASKPASS git pull --rebase || true; \
	GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=$$GIT_ASKPASS git push origin main; \
	echo "GitOps content pushed to $$GITOPS_REPO_URL"

gitops-repo-clean: ## Remove stray non-kustomize files from GitOps repo roots
	@GITHUB_OWNER=$${GITHUB_OWNER:-metasync}; \
	GITOPS_REPO_NAME=$${GITOPS_REPO_NAME:-luban-hello-world-py-gitops}; \
	GITOPS_REPO_URL=https://github.com/$$GITHUB_OWNER/$$GITOPS_REPO_NAME.git; \
	TMP_DIR=$$(mktemp -d); \
	git clone $$GITOPS_REPO_URL $$TMP_DIR/repo >/dev/null 2>&1; \
	cd $$TMP_DIR/repo; \
	rm -f app/deployment.yaml app/kustomization.yaml argocd/application.yaml argocd/kustomization.yaml || true; \
	git config user.name "Luban CI"; \
	git config user.email "ci@luban.com"; \
	git add -A; \
	git commit -m "Remove stray non-kustomize root files" || true; \
	if [ -z "$$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN is required"; exit 1; fi; \
	GIT_ASKPASS=$$(mktemp); \
	printf '#!/bin/sh\necho $$GITHUB_TOKEN\n' > $$GIT_ASKPASS; \
	chmod +x $$GIT_ASKPASS; \
	GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=$$GIT_ASKPASS git push origin main || true; \
	echo "GitOps repo cleaned: $$GITOPS_REPO_URL"
gitops-repo-verify: ## Verify GitOps repo structure
	@GITHUB_OWNER=$${GITHUB_OWNER:-metasync}; \
	GITOPS_REPO_NAME=$${GITOPS_REPO_NAME:-luban-hello-world-py-gitops}; \
	GITOPS_REPO_URL=https://github.com/$$GITHUB_OWNER/$$GITOPS_REPO_NAME.git; \
	TMP_DIR=$$(mktemp -d); \
	git clone $$GITOPS_REPO_URL $$TMP_DIR/repo >/dev/null 2>&1; \
	echo "Tree under app/:"; \
	find $$TMP_DIR/repo/app -maxdepth 2 -type f -print | sed 's#^.*/repo/##'; \
	echo "Tree under argocd/:"; \
	find $$TMP_DIR/repo/argocd -maxdepth 2 -type f -print | sed 's#^.*/repo/##'

argocd-apply-snd: ## Apply Argo CD Application from per-app GitOps snd overlay
	@GITOPS_REPO_URL=$${GITOPS_REPO_URL:-https://github.com/metasync/luban-hello-world-py-gitops.git}; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py-snd\n  namespace: argocd\nspec:\n  project: devops-snd\n  source:\n    repoURL: %s\n    targetRevision: main\n    path: app/overlays/snd\n  destination:\n    server: https://kubernetes.default.svc\n    namespace: luban-ci\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n    - CreateNamespace=true\n" "$$GITOPS_REPO_URL" | kubectl apply -f -

argocd-apply-prd: ## Apply Argo CD Application from per-app GitOps prd overlay
	@GITOPS_REPO_URL=$${GITOPS_REPO_URL:-https://github.com/metasync/luban-hello-world-py-gitops.git}; \
	printf "apiVersion: argoproj.io/v1alpha1\nkind: Application\nmetadata:\n  name: luban-hello-world-py-prd\n  namespace: argocd\nspec:\n  project: devops-prd\n  source:\n    repoURL: %s\n    targetRevision: main\n    path: app/overlays/prd\n  destination:\n    server: https://kubernetes.default.svc\n    namespace: luban-ci\n  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n    - CreateNamespace=true\n" "$$GITOPS_REPO_URL" | kubectl apply -f -
