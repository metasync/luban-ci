FROM python:3.12-alpine

# Install system dependencies
RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache curl jq git openssh-client

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create a non-root user (uid 1000) for SSH compatibility
RUN adduser -D -u 1000 luban

# Install kubectl
ARG KUBECTL_VERSION=v1.35.1
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

WORKDIR /app

# Install python dependencies (caching step)
COPY pyproject.toml uv.lock ./
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-install-project

# Copy tool code
COPY . .

# Install the project itself to enable [project.scripts]
# Dependencies are already cached/installed
# We need to run sync again to install the project package
RUN uv sync --frozen

# Set environment variables
# Ensure the bin directory is in PATH so uv run can find the script
ENV PATH="/app/.venv/bin:$PATH"

# Ensure non-root user owns the app directory and venv
RUN chown -R luban:luban /app

# Set entrypoint to use the installed script directly
# The venv bin directory is in PATH
# We use the installed script directly since it's in PATH
ENTRYPOINT ["luban-provisioner"]

# Run as non-root user
USER 1000
