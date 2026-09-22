#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"

def set_value(lines, key, value):
    prefix = key + "="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = prefix + value
            return lines
    lines.append(prefix + value)
    return lines

print("\n=== Mini-Jarvis First-Time Setup ===\n")
print("Your API key is entered locally on this phone and is NOT sent to this setup script.\n")

try:
    api = input("Paste your OpenAI API key (input hidden is not available in all Termux shells): ").strip()
except (KeyboardInterrupt, EOFError):
    print("\nSetup cancelled.")
    raise SystemExit(1)

if not api:
    print("No API key entered.")
    raise SystemExit(1)

try:
    password = input("Create a Mini-Jarvis access password: ").strip()
except (KeyboardInterrupt, EOFError):
    print("\nSetup cancelled.")
    raise SystemExit(1)

if not password:
    password = "change-me"

if ENV.exists():
    lines = ENV.read_text(encoding="utf-8").splitlines()
else:
    example = ROOT / ".env.example"
    lines = example.read_text(encoding="utf-8").splitlines() if example.exists() else []

lines = set_value(lines, "OPENAI_API_KEY", api)
lines = set_value(lines, "APP_PASSWORD", password)

ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
try:
    os.chmod(ENV, 0o600)
except OSError:
    pass

print("\nSetup complete.")
print("Your key is stored locally in .env.")
print("Start Mini-Jarvis with: ./run.sh\n")
