#!/bin/bash
# Download a Sculptor AppImage from S3, extract the backend + sculpt CLI
# binaries to /opt/sculptor, and clean up.
#
# Usage: ./install-sculptor.sh <version|latest>
set -euo pipefail

S3_BASE_URL="https://imbue-sculptor-releases.s3.us-west-2.amazonaws.com/slim"
VERSION="${1:?Usage: $0 <version|latest>}"

MACHINE=$(uname -m)
case "$MACHINE" in
  x86_64)  ARCH="x64";  MANIFEST="AppImage/x64/latest-linux.yml" ;;
  aarch64) ARCH="arm64"; MANIFEST="AppImage/arm64/latest-linux-arm64.yml" ;;
  *)       echo "Unsupported arch: $MACHINE" >&2; exit 1 ;;
esac

if [ "$VERSION" = "latest" ]; then
  VERSION=$(curl -fsSL "$S3_BASE_URL/$MANIFEST" | grep '^version:' | awk '{print $2}')
  echo "Resolved latest version: $VERSION"
fi

FILENAME="Sculptor-${VERSION}.AppImage"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "Downloading $FILENAME..."
curl -fSL --progress-bar -o "$WORK/$FILENAME" "$S3_BASE_URL/AppImage/$ARCH/$FILENAME"
chmod +x "$WORK/$FILENAME"

echo "Extracting..."
(cd "$WORK" && "./$FILENAME" --appimage-extract >/dev/null)

RESOURCES="$WORK/squashfs-root/usr/lib/sculptor/resources"
mkdir -p /opt/sculptor
cp -a "$RESOURCES/sculptor_backend" /opt/sculptor/
cp -a "$RESOURCES/sculpt" /opt/sculptor/
chmod +x /opt/sculptor/sculptor_backend/sculptor_backend /opt/sculptor/sculpt/sculpt
echo "$VERSION" > /opt/sculptor/.sculptor-version

echo "Installed sculptor $VERSION to /opt/sculptor"
