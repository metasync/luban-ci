# Manifests Deployment Makefile

include Makefile.env
export

.PHONY: deploy clean logs

deploy: ## Deploy Argo Workflow Template and RBAC
	@echo "Deploying Workflow RBAC..."
	@kubectl apply -f pipeline-sa.yaml
	@echo "Deploying kpack Stack and Builder..."
	@kubectl apply -f kpack-stack.yaml
	@kubectl apply -f kpack-builder.yaml
	@echo "Applying Argo Workflow semaphores..."
	@kubectl apply -f argo-semaphore.yaml
	@echo "Applying Luban Configuration..."
	@kubectl apply -f luban-config.yaml
	@echo "Deploying Workflow Templates..."
	@kubectl apply -f luban-ci-kpack-workflow-template.yaml
	@kubectl apply -f argocd-project-workflow-template.yaml
	@kubectl apply -f argocd-app-workflow-template.yaml
	@kubectl apply -f harbor-project-workflow-template.yaml
	@kubectl apply -f gitops-repo-workflow-template.yaml
	@kubectl apply -f gitops-helper-workflow-template.yaml
	@kubectl apply -f luban-project-workflow-template.yaml
	@kubectl apply -f luban-app-workflow-template.yaml
	@echo "Deploying Cleanup CronWorkflow..."
	@kubectl apply -f workflow-cleanup-cron.yaml
	@echo "Pipeline deployed."

clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)

logs: ## Show logs for the latest kpack build of the app
	@echo "Fetching logs for $(APP_NAME) in $(K8S_NAMESPACE)..."
	@kp build logs $(APP_NAME) -n $(K8S_NAMESPACE)
