# Test Management Makefile

include Makefile.env
export

.PHONY: test-ci-pipeline test-webhook test-webhook-py

test-ci-pipeline: ## Trigger the kpack CI Workflow using Argo CLI
	@echo "Triggering kpack CI Workflow via Argo CLI..."
	@argo submit -n $(K8S_NAMESPACE) \
		--from wftmpl/luban-ci-kpack-template \
		-p repo_url=$(REPO_URL) \
		-p app_name=$(APP_NAME) \
		-p revision=$(REVISION) \
		-p tag=$(TAG) \
		-p project_name=$(PROJECT_NAME) \
		--watch

test-webhook-py: ## Send signed push payload via gateway to trigger Workflow (Python)
	@echo "Running webhook test script (Python)..."
	@python3 webhook_test.py

test-webhook: ## Send signed push payload via gateway to trigger Workflow (Shell)
	@echo "Running webhook test script (Shell)..."
	@./webhook_test.sh

test-get-token: ## Generate login token for test users (ADMIN or DEVELOPER)
	@echo "Generating token for test-project-$(ROLE) in $(TEST_NAMESPACE)..."
	@if [ -z "$(ROLE)" ]; then echo "Error: Please specify ROLE=admin or ROLE=developer"; exit 1; fi
	@kubectl create token test-project-$(ROLE) -n $(TEST_NAMESPACE) --duration=24h

test-rbac-validation: ## Validate permissions for test users
	@echo "Validating RBAC for $(TEST_NAMESPACE)..."
	@echo "\n--- Admin User (test-project-admin) ---"
	@echo "Can delete workflows? (Expected: yes)"
	@kubectl auth can-i delete workflow --as=system:serviceaccount:$(TEST_NAMESPACE):test-project-admin -n $(TEST_NAMESPACE)
	@echo "Can submit workflows? (Expected: yes)"
	@kubectl auth can-i create workflow --as=system:serviceaccount:$(TEST_NAMESPACE):test-project-admin -n $(TEST_NAMESPACE)
	@echo "\n--- Developer User (test-project-developer) ---"
	@echo "Can delete workflows? (Expected: no)"
	@kubectl auth can-i delete workflow --as=system:serviceaccount:$(TEST_NAMESPACE):test-project-developer -n $(TEST_NAMESPACE)
	@echo "Can submit workflows? (Expected: yes)"
	@kubectl auth can-i create workflow --as=system:serviceaccount:$(TEST_NAMESPACE):test-project-developer -n $(TEST_NAMESPACE)
