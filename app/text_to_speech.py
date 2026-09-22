import subprocess
import tempfile
import os

async def speak(text: str) -> bytes | None:
    if not text.strip():
        return None

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    try:
        subprocess.run(
            ["espeak", "-p", "0.5", "-s", "135", text.strip()[:500], "-w", path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
