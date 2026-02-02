# Events Management Makefile

include Makefile.env
export

.PHONY: deploy webhook-secret webhook-secret-rotate

deploy: ## Deploy Argo Events (EventBus, EventSource, Sensor)
	@echo "Deploying Argo Events..."
	@kubectl apply -f eventbus.yaml
	@kubectl apply -f github-event-source.yaml
	@kubectl apply -f github-sensor.yaml
	@kubectl apply -f gateway.yaml
	@echo "Argo Events deployed."

webhook-secret: ## Ensure GitHub webhook secret exists (skip if present)
	@if kubectl get secret github-webhook-secret -n $(K8S_NAMESPACE) >/dev/null 2>&1; then \
		echo "Webhook secret 'github-webhook-secret' already exists in $(K8S_NAMESPACE). Skipping generation."; \
		echo "Use 'make events-webhook-secret-rotate' to force rotation."; \
	else \
		$(MAKE) webhook-secret-rotate; \
	fi

webhook-secret-rotate: ## Force generate and rotate GitHub webhook secret
	@echo "Generating webhook secret for namespace $(K8S_NAMESPACE)..."
	@SECRET=$$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32); \
	kubectl delete secret github-webhook-secret -n $(K8S_NAMESPACE) --ignore-not-found; \
	kubectl create secret generic github-webhook-secret -n $(K8S_NAMESPACE) --from-literal=secret="$$SECRET"; \
	echo "Webhook secret created in K8s. Use this exact value in GitHub webhook settings:"; \
	echo "$$SECRET"
