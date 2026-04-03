# Sculptor backend for OpenHost — packaged release
#
# Downloads a pre-built Sculptor AppImage from S3, extracts the
# self-contained PyInstaller binaries, and runs them directly.
#
# Build arg:
#   SCULPTOR_VERSION — release version to download (default: 0.20.0)
#                      Use "latest" to fetch the current stable release.

FROM ubuntu:24.04

ARG SCULPTOR_VERSION=0.20.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    python3 \
    supervisor \
    jq \
    vim \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (remove default ubuntu user which holds UID 1000)
RUN userdel -r ubuntu 2>/dev/null || true && \
    useradd -m -d /home/devuser -s /bin/bash -u 1000 devuser

# Download the AppImage, extract sculptor_backend + sculpt CLI, clean up.
# All in one RUN so the ~500MB AppImage + squashfs extraction don't bloat the layer.
RUN set -eux; \
    S3_BASE_URL="https://imbue-sculptor-releases.s3.us-west-2.amazonaws.com/slim"; \
    MACHINE=$(uname -m); \
    case "$MACHINE" in \
      x86_64)  ARCH="x64"; MANIFEST_PATH="AppImage/x64/latest-linux.yml" ;; \
      aarch64) ARCH="arm64"; MANIFEST_PATH="AppImage/arm64/latest-linux-arm64.yml" ;; \
      *) echo "Unsupported arch: $MACHINE" && exit 1 ;; \
    esac; \
    VERSION="$SCULPTOR_VERSION"; \
    if [ "$VERSION" = "latest" ]; then \
      VERSION=$(curl -fsSL "$S3_BASE_URL/$MANIFEST_PATH" | grep '^version:' | awk '{print $2}'); \
      echo "Resolved latest version: $VERSION"; \
    fi; \
    FILENAME="Sculptor-${VERSION}.AppImage"; \
    cd /tmp && \
    curl -fSL --progress-bar -o "$FILENAME" "$S3_BASE_URL/AppImage/$ARCH/$FILENAME" && \
    chmod +x "$FILENAME" && \
    "./$FILENAME" --appimage-extract && \
    RESOURCES="/tmp/squashfs-root/usr/lib/sculptor/resources" && \
    mkdir -p /opt/sculptor && \
    cp -a "$RESOURCES/sculptor_backend" /opt/sculptor/ && \
    cp -a "$RESOURCES/sculpt" /opt/sculptor/ && \
    chmod +x /opt/sculptor/sculptor_backend/sculptor_backend /opt/sculptor/sculpt/sculpt && \
    echo "$VERSION" > /opt/sculptor/.sculptor-version && \
    rm -rf /tmp/Sculptor-*.AppImage /tmp/squashfs-root

# Install Claude Code CLI (not auto-installed in sculptor 0.20.0).
RUN curl -fsSL https://claude.ai/install.sh | bash && \
    cp /root/.local/bin/claude /usr/local/bin/claude && \
    chmod +x /usr/local/bin/claude && \
    rm -rf /root/.claude /root/.local/bin/claude

# Setup scripts for secrets and Git
COPY openhost/setup/ /app/setup/
COPY openhost/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/setup/*.sh

# Supervisord config
COPY openhost/supervisord.conf /etc/supervisor/conf.d/sculptor.conf

# Sculptor serves directly on port 8080 (the externally-exposed port).
ENV SCULPTOR_PORT=8080
ENV SCULPTOR_API_PORT=8080
ENV SCULPTOR_BIND_HOST=0.0.0.0

# Data persistence: OpenHost provides OPENHOST_APP_DATA_DIR and
# OPENHOST_APP_TEMP_DIR at runtime. We set defaults here so the
# container also works standalone (e.g. for local testing).
ENV OPENHOST_APP_DATA_DIR=/data/app_data/sculptor
ENV OPENHOST_APP_TEMP_DIR=/data/app_temp_data/sculptor
RUN mkdir -p /data/app_data/sculptor /data/app_temp_data/sculptor && \
    chown -R devuser:devuser /data

USER root

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
