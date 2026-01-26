# Events Management Makefile

include Makefile.env
export

.PHONY: deploy webhook-secret

deploy: ## Deploy Argo Events (EventBus, EventSource, Sensor)
	@echo "Deploying Argo Events..."
	@kubectl apply -f eventbus.yaml
	@kubectl apply -f event-source.yaml
	@kubectl apply -f sensor.yaml
	@kubectl apply -f gateway.yaml
	@echo "Argo Events deployed."

webhook-secret: ## Generate and create GitHub webhook secret in K8s
	@echo "Generating webhook secret for namespace $(K8S_NAMESPACE)..."
	@SECRET=$$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32); \
	kubectl delete secret github-webhook-secret -n $(K8S_NAMESPACE) --ignore-not-found; \
	kubectl create secret generic github-webhook-secret -n $(K8S_NAMESPACE) --from-literal=secret="$$SECRET"; \
	echo "Webhook secret created in K8s. Use this exact value in GitHub webhook settings:"; \
	echo "$$SECRET"
