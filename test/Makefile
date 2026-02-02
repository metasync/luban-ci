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
		--watch

test-webhook-py: ## Send signed push payload via gateway to trigger Workflow (Python)
	@echo "Running webhook test script (Python)..."
	@python3 webhook_test.py

test-webhook: ## Send signed push payload via gateway to trigger Workflow (Shell)
	@echo "Running webhook test script (Shell)..."
	@./webhook_test.sh
