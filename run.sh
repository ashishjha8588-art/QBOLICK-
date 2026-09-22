#!/bin/sh
set -e
cd "$(dirname "$0")"

if [ ! -f .env ] || ! grep -q '^GROQ_API_KEY=.' .env 2>/dev/null; then
  python3 first_run_setup.py
fi

if [ ! -d .venv ]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

. .venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
