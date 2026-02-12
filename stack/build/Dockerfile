FROM quay.io/luban-ci/luban-base:al2023

# Install build dependencies
RUN dnf install -y \
    git \
    wget \
    tar \
    gzip \
    which \
    gcc \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel && \
    dnf clean all

# Set user to cnb
USER cnb

# Set working directory
WORKDIR /workspace
