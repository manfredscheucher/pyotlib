#!/usr/bin/env bash
# Install git hooks for pyotlib2.
# Run once after cloning:  bash scripts/install-hooks.sh

set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

# ── pre-commit ────────────────────────────────────────────────────────────────
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/usr/bin/env bash
# Runs the full CI test suite inside Docker before every commit.
# Requires Docker Desktop (https://www.docker.com/products/docker-desktop/).
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
IMAGE="pyotlib2-ci"

# Check Docker is available
if ! docker info &>/dev/null; then
    echo "✗ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "▶ Building CI image (python:3.12-slim) …"
docker build -q -f "$REPO_ROOT/Dockerfile.ci" -t "$IMAGE" "$REPO_ROOT"

echo "▶ Running tests …"
docker run --rm "$IMAGE"
echo "✓ All tests passed."
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "✓ pre-commit hook installed."
echo ""
echo "The hook runs 'pytest' inside Docker (identical to GitHub CI) before each commit."
echo "To skip it once:  git commit --no-verify"
