#!/usr/bin/env bash
# Installs deps and builds dist/ only when needed (missing or older than sources).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then
  npm ci --no-audit --no-fund --loglevel=error
  touch node_modules
fi
if [ ! -f dist/index.html ] || [ -n "$(find src index.html vite.config.ts tsconfig.json package.json -newer dist/index.html -print -quit)" ]; then
  npm run --silent build
fi
