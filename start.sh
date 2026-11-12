#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  echo 'Missing .env. Run: bash termux/setup.sh'
  exit 1
fi
mkdir -p data workspace
exec python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}"
