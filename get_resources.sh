#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES_DIR="${BASE_DIR}/resources"

mkdir -p "${RESOURCES_DIR}"
cd "${RESOURCES_DIR}"

fetch() {
  local url="$1"
  local out="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --retry 3 --retry-delay 1 -o "${out}" "${url}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q --show-progress -O "${out}" "${url}"
  else
    echo "error: need curl or wget to download resources" >&2
    return 1
  fi
}

# Python embeddable (Windows)
PYTHON3_VERSION="${PYTHON3_VERSION:-3.14.2}"
PYTHON3_ARCH="${PYTHON3_ARCH:-amd64}"
PYTHON3_FILENAME="python-${PYTHON3_VERSION}-embed-${PYTHON3_ARCH}.zip"
PYTHON3_URL="https://www.python.org/ftp/python/${PYTHON3_VERSION}/${PYTHON3_FILENAME}"

if [[ ! -f "${PYTHON3_FILENAME}" ]]; then
  fetch "${PYTHON3_URL}" "${PYTHON3_FILENAME}"
  echo "[+] Python3 Embed";
else
  echo "[*] Python3 Embed";
fi

# Serve a stable name expected by stagers.
if ! ln -sf "${PYTHON3_FILENAME}" "python3.zip" 2>/dev/null; then
  cp -f "${PYTHON3_FILENAME}" "python3.zip"
fi

# Reverse proxy
if [[ ! -d "Invoke-SocksProxy/.git" ]]; then
  git clone "https://github.com/p3nt4/Invoke-SocksProxy"
  echo "[+] Invoke-SocksProxy";
else
  echo "[*] Invoke-SocksProxy";
fi
