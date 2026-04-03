# Sculptor backend for OpenHost — packaged release
#
# Instead of building from source, this Dockerfile downloads a pre-built
# Sculptor AppImage from S3, extracts the self-contained PyInstaller
# binaries (sculptor_backend + sculpt CLI), and runs them directly.
#
# Build arg:
#   SCULPTOR_VERSION — release version to download (default: 0.20.0)
#                      Use "latest" to fetch the current stable release.

# ---------------------------------------------------------------------------
# Stage 1: download — fetch and extract the AppImage (Linux required)
# ---------------------------------------------------------------------------
FROM ubuntu:24.04 AS download

ARG SCULPTOR_VERSION=0.20.0
ARG SCULPTOR_CHANNEL=slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    file \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/download

# Download and extract the AppImage
RUN set -eux; \
    S3_BASE_URL="https://imbue-sculptor-releases.s3.us-west-2.amazonaws.com"; \
    MACHINE=$(uname -m); \
    case "$MACHINE" in \
      x86_64)  ARCH="x64"; MANIFEST_PATH="AppImage/x64/latest-linux.yml" ;; \
      aarch64) ARCH="arm64"; MANIFEST_PATH="AppImage/arm64/latest-linux-arm64.yml" ;; \
      *) echo "Unsupported arch: $MACHINE" && exit 1 ;; \
    esac; \
    VERSION="$SCULPTOR_VERSION"; \
    if [ "$VERSION" = "latest" ]; then \
      MANIFEST_URL="${S3_BASE_URL}/${SCULPTOR_CHANNEL}/${MANIFEST_PATH}"; \
      VERSION=$(curl -fsSL "$MANIFEST_URL" | grep '^version:' | awk '{print $2}'); \
      echo "Resolved latest version: $VERSION"; \
    fi; \
    FILENAME="Sculptor-${VERSION}.AppImage"; \
    DOWNLOAD_URL="${S3_BASE_URL}/${SCULPTOR_CHANNEL}/AppImage/${ARCH}/${FILENAME}"; \
    echo "Downloading $DOWNLOAD_URL"; \
    curl -fSL --progress-bar -o "$FILENAME" "$DOWNLOAD_URL"; \
    chmod +x "$FILENAME"; \
    "./$FILENAME" --appimage-extract; \
    echo "$VERSION" > /tmp/sculptor-version

# Copy out the backend and sculpt CLI binaries
RUN set -eux; \
    RESOURCES="/tmp/download/squashfs-root/usr/lib/sculptor/resources"; \
    mkdir -p /opt/sculptor/sculptor_backend /opt/sculptor/sculpt; \
    cp -a "$RESOURCES/sculptor_backend/." /opt/sculptor/sculptor_backend/; \
    chmod +x /opt/sculptor/sculptor_backend/sculptor_backend; \
    if [ -d "$RESOURCES/sculpt" ]; then \
      cp -a "$RESOURCES/sculpt/." /opt/sculptor/sculpt/; \
      chmod +x /opt/sculptor/sculpt/sculpt; \
    fi; \
    cp /tmp/sculptor-version /opt/sculptor/.sculptor-version

# ---------------------------------------------------------------------------
# Stage 2: runtime — slim image with only what's needed to run
# ---------------------------------------------------------------------------
FROM ubuntu:24.04

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

# Copy pre-built binaries from download stage
COPY --from=download /opt/sculptor /opt/sculptor

# Install Claude Code CLI (not auto-installed in sculptor 0.20.0).
# Install as root first, then copy the binary to a shared location.
RUN curl -fsSL https://claude.ai/install.sh | bash && \
    cp /root/.claude/local/claude /usr/local/bin/claude && \
    chmod +x /usr/local/bin/claude && \
    rm -rf /root/.claude

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

# Entrypoint runs as root (needs usermod, chown, supervisord)
USER root

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
