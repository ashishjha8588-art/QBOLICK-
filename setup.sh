#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
python -m pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env. Edit it and add your GROQ_API_KEY and APP_PASSWORD."
else
  echo ".env already exists; leaving it unchanged."
fi
