FROM python:3.12-alpine

# Install system dependencies
# curl: for downloading kubectl
# jq: for JSON processing in secret copying
# git: for initializing and pushing repositories
# openssh-client: for git ssh operations
RUN apk add --no-cache curl jq git openssh-client

# Create a non-root user (uid 1000) for SSH compatibility
RUN adduser -D -u 1000 luban

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Install python dependencies directly
RUN pip install --no-cache-dir cookiecutter click requests ruamel.yaml

# Workdir
WORKDIR /app

# Copy tool code
COPY . .

# Set PYTHONPATH to include src
ENV PYTHONPATH=/app/src

# Set HOME to /tmp because tools like Cookiecutter need a writable home directory.
# When running in Argo Workflows or restricted security contexts (non-root),
# the default HOME (/) is often read-only.
ENV HOME=/tmp

# Set entrypoint
ENTRYPOINT ["python3", "/app/src/main.py"]
