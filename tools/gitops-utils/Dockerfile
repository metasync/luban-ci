FROM alpine:3.23
ARG ARGO_VERSION=latest
ARG KP_VERSION=0.17.1
LABEL org.opencontainers.image.version=${ARGO_VERSION}
RUN apk add --no-cache ca-certificates git openssh yq curl kubectl jq
# Install Argo CLI
RUN curl -sLO https://github.com/argoproj/argo-workflows/releases/download/${ARGO_VERSION}/argo-linux-amd64.gz && \
    gunzip argo-linux-amd64.gz && \
    chmod +x argo-linux-amd64 && \
    mv argo-linux-amd64 /usr/local/bin/argo
# Install kp CLI
RUN curl -L https://github.com/buildpacks-community/kpack-cli/releases/download/v${KP_VERSION}/kp-linux-amd64-${KP_VERSION} -o /usr/local/bin/kp && \
    chmod +x /usr/local/bin/kp

# Install Crane (go-containerregistry)
RUN curl -sL "https://github.com/google/go-containerregistry/releases/download/v0.19.1/go-containerregistry_Linux_x86_64.tar.gz" > go-containerregistry.tar.gz && \
    tar -zxvf go-containerregistry.tar.gz -C /usr/local/bin/ crane && \
    chmod +x /usr/local/bin/crane && \
    rm go-containerregistry.tar.gz

RUN adduser -D -u 1000 luban
USER 1000
