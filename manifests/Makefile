# Manifests Deployment Makefile

include Makefile.env
export

.PHONY: deploy clean logs tunnel-setup

deploy: ## Deploy Argo Workflow Template and RBAC
	@echo "Deploying Workflow RBAC..."
	@kubectl apply -f rbac/pipeline-sa.yaml
	@kubectl apply -f rbac/kpack-admin-role.yaml
	@kubectl apply -f rbac/luban-view-templates-clusterrole.yaml
	@echo "Deploying kpack Stack and Builder..."
	@kubectl apply -f kpack/kpack-stack.yaml
	@kubectl apply -f kpack/kpack-builder.yaml
	@echo "Applying Global Workflow Restrictions (argo namespace)..."
	@# Check for legacy config conflict
	@if [ -n "$$(kubectl get cm argo-workflows-workflow-controller-configmap -n argo -o jsonpath='{.data.config}' 2>/dev/null)" ]; then \
		echo "Removing legacy 'config' key to prevent conflict..."; \
		kubectl patch configmap argo-workflows-workflow-controller-configmap -n argo --type=json -p='[{"op": "remove", "path": "/data/config"}]'; \
	fi
	@kubectl apply -f config/global-workflow-restrictions.yaml || echo "Warning: Failed to apply global config. Ensure you have admin access to 'argo' namespace."
	@echo "Applying Luban Configuration..."
	@kubectl apply -f config/luban-config.yaml
	@kubectl apply -f config/git-providers.yaml
	@echo "Deploying Workflow Templates..."
	@kubectl apply -f workflows/luban-ci-kpack-workflow-template.yaml
	@kubectl apply -f workflows/argocd-project-workflow-template.yaml
	@kubectl apply -f workflows/argocd-app-workflow-template.yaml
	@kubectl apply -f workflows/harbor-project-workflow-template.yaml
	@kubectl apply -f workflows/namespace-provision-workflow-template.yaml
	@kubectl apply -f workflows/gitops-repo-workflow-template.yaml
	@kubectl apply -f workflows/source-repo-workflow-template.yaml
	@kubectl apply -f workflows/luban-project-workflow-template.yaml
	@kubectl apply -f workflows/luban-app-workflow-template.yaml
	@kubectl apply -f workflows/luban-promotion-workflow-template.yaml
	@kubectl apply -f workflows/luban-pipeline-dispatcher-template.yaml
	@echo "Pipeline deployed."

clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)

logs: ## Show logs for the latest kpack build of the app
	@echo "Fetching logs for $(APP_NAME) in $(K8S_NAMESPACE)..."
	@kp build logs $(APP_NAME) -n $(K8S_NAMESPACE)

tunnel-setup: ## Setup Cloudflare Tunnel for webhook exposure (optional)
	@./tunnel/setup.sh
