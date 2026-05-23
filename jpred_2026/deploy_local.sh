#!/bin/bash
# Deploy the built docs to the repository's GitHub Pages tree.
#
# Source:      jpred_2026/docs/
# Destination: docs/2026/  (relative to the repository root)
#
# Run build_preds.sh first to ensure docs/ is up to date before deploying.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SRC="${SCRIPT_DIR}/docs/"
DEST="${REPO_ROOT}/docs/2026/"

echo "Source:      ${SRC}"
echo "Destination: ${DEST}"
echo ""

mkdir -p "${DEST}"

rsync -av --delete "${SRC}" "${DEST}"

echo ""
echo "Deployed to ${DEST}"
