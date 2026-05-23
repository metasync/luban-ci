# Manifests Deployment Makefile

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
include $(ROOT_DIR)/Makefile.env
-include Makefile.env
export

.PHONY: deploy deploy-rbac deploy-kpack deploy-global-argo-config deploy-config deploy-workflows verify clean logs tunnel-setup secrets secrets-dry-run

deploy: ## Deploy Argo Workflow Template and RBAC
	@$(MAKE) deploy-rbac
	@$(MAKE) deploy-kpack
	@$(MAKE) deploy-global-argo-config
	@$(MAKE) deploy-config
	@$(MAKE) deploy-workflows
	@echo "Pipeline deployed."

deploy-rbac:
	@echo "Deploying Workflow RBAC..."
	@kubectl apply -f rbac/pipeline-sa.yaml
	@kubectl apply -f rbac/kpack-admin-role.yaml
	@kubectl apply -f rbac/argo-controller-role.yaml
	@kubectl apply -f rbac/luban-view-templates-clusterrole.yaml

deploy-kpack:
	@echo "Deploying kpack Stack and Builder..."
	@kubectl apply -f kpack/kpack-lifecycle.yaml
	@kubectl apply -f kpack/kpack-stack.yaml
	@kubectl apply -f kpack/kpack-builder.yaml

deploy-global-argo-config:
	@echo "Applying Global Workflow Restrictions (argo namespace)..."
	@# Check for legacy config conflict
	@if [ -n "$$(kubectl get cm argo-workflows-workflow-controller-configmap -n argo -o jsonpath='{.data.config}' 2>/dev/null)" ]; then \
		echo "Removing legacy 'config' key to prevent conflict..."; \
		kubectl patch configmap argo-workflows-workflow-controller-configmap -n argo --type=json -p='[{"op": "remove", "path": "/data/config"}]'; \
	fi
	@kubectl apply -f config/global-workflow-restrictions.yaml || echo "Warning: Failed to apply global config. Ensure you have admin access to 'argo' namespace."

deploy-config:
	@echo "Applying Luban Configuration..."
	@kubectl apply -f config/luban-config.yaml
	@kubectl apply -f config/luban-python-config.yaml
	@kubectl apply -f config/luban-dagster-config.yaml

deploy-workflows:
	@echo "Deploying Workflow Templates..."
	@kubectl apply -f workflows/luban-ci-kpack-workflow-template.yaml
	@kubectl apply -f workflows/argocd-project-workflow-template.yaml
	@kubectl apply -f workflows/argocd-app-workflow-template.yaml
	@kubectl apply -f workflows/ci-infra-provision-workflow-template.yaml
	@kubectl apply -f workflows/harbor-project-workflow-template.yaml
	@kubectl apply -f workflows/namespace-provision-workflow-template.yaml
	@kubectl apply -f workflows/infra-repo-update-workflow-template.yaml
	@kubectl apply -f workflows/luban-infra-setup-workflow-template.yaml
	@kubectl apply -f workflows/gitops-repo-workflow-template.yaml
	@kubectl apply -f workflows/source-repo-workflow-template.yaml
	@kubectl apply -f workflows/luban-project-workflow-template.yaml
	@kubectl apply -f workflows/luban-python-app-workflow-template.yaml
	@kubectl apply -f workflows/luban-dagster-code-location-workflow-template.yaml
	@kubectl apply -f workflows/luban-dagster-dbt-starrocks-code-location-workflow-template.yaml
	@kubectl apply -f workflows/luban-dagster-platform-setup-template.yaml
	@kubectl apply -f workflows/luban-promotion-workflow-template.yaml
	@kubectl apply -f workflows/luban-pipeline-dispatcher-template.yaml

verify:
	@kubectl -n $(K8S_NAMESPACE) get sa luban-ci-sa >/dev/null
	@kubectl -n $(K8S_NAMESPACE) get configmap luban-config >/dev/null
	@kubectl get clusterworkflowtemplate luban-ci-kpack-template >/dev/null
	@kubectl get clusterworkflowtemplate luban-promotion-template >/dev/null
	@kubectl get clusterlifecycle default-lifecycle >/dev/null
	@kubectl get clusterstack luban-stack >/dev/null
	@kubectl get clusterstore luban-store >/dev/null
	@kubectl get clusterbuilder luban-builder >/dev/null
	@echo "OK: pipeline resources present"

secrets: ## Create/Update Kubernetes secrets from env files
	@./secrets/setup-secrets.sh

secrets-dry-run: ## Validate secret templates render (does not write to cluster)
	@./secrets/setup-secrets.sh --dry-run

clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)

logs: ## Show logs for the latest kpack build of the app
	@if [ -z "$(APP_NAME)" ]; then echo "Error: APP_NAME is required. Usage: make pipeline-logs APP_NAME=my-app"; exit 1; fi
	@echo "Fetching logs for $(APP_NAME) in $(K8S_NAMESPACE)..."
	@kp build logs $(APP_NAME) -n $(K8S_NAMESPACE)

tunnel-setup: ## Setup Cloudflare Tunnel for webhook exposure (optional)
	@./tunnel/setup.sh
