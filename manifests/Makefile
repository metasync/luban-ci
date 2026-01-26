# Manifests Deployment Makefile

include Makefile.env
export

.PHONY: deploy clean

deploy: ## Deploy Argo Workflow Template and RBAC
	@echo "Deploying Workflow RBAC..."
	@kubectl apply -f pipeline-sa.yaml
	@echo "Deploying kpack Stack and Builder..."
	@kubectl apply -f kpack-stack.yaml
	@kubectl apply -f kpack-builder.yaml
	@echo "Applying Argo Workflow semaphores..."
	@kubectl apply -f argo-semaphore.yaml
	@echo "Deploying Workflow Templates..."
	@kubectl apply -f ci-kpack-workflow-template.yaml
	@kubectl apply -f argocd-project-workflow-template.yaml
	@echo "Deploying Cleanup CronWorkflow..."
	@kubectl apply -f workflow-cleanup-cron.yaml
	@echo "Pipeline deployed."

clean: ## Delete all workflows
	@kubectl delete wf --all -n $(K8S_NAMESPACE)
