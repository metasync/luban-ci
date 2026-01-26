FROM alpine:3.23
ARG ARGO_VERSION=latest
LABEL org.opencontainers.image.version=${ARGO_VERSION}
RUN apk add --no-cache ca-certificates git openssh yq curl
# Install Argo CLI
RUN curl -sLO https://github.com/argoproj/argo-workflows/releases/download/${ARGO_VERSION}/argo-linux-amd64.gz && \
    gunzip argo-linux-amd64.gz && \
    chmod +x argo-linux-amd64 && \
    mv argo-linux-amd64 /usr/local/bin/argo
RUN adduser -D -u 1000 luban
USER 1000
