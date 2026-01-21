# Base image: Amazon Linux 2023 Minimal
FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal

# Set CNB user/group IDs
ARG cnb_uid=1000
ARG cnb_gid=1000
ARG stack_id="io.buildpacks.stacks.luban"

# Install common packages
# shadow-utils: for useradd/groupadd
# ca-certificates: for SSL connections
RUN dnf install -y shadow-utils ca-certificates && \
    dnf clean all

# Create cnb user and group
RUN groupadd cnb --gid ${cnb_gid} && \
    useradd --uid ${cnb_uid} --gid ${cnb_gid} -m -s /bin/bash cnb

# Set CNB environment variables
ENV CNB_USER_ID=${cnb_uid}
ENV CNB_GROUP_ID=${cnb_gid}
ENV CNB_STACK_ID=${stack_id}

# Set labels conforming to Buildpacks spec
LABEL io.buildpacks.stack.id=${stack_id} \
      io.buildpacks.stack.description="Amazon Linux 2023 Minimal Stack" \
      io.buildpacks.stack.distro.name="Amazon Linux" \
      io.buildpacks.stack.distro.version="2023" \
      io.buildpacks.stack.homepage="https://github.com/metasync/luban-ci" \
      io.buildpacks.stack.maintainer="Metasync"
