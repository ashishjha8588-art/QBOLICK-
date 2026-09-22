# Mini-Jarvis — Phone/API Package

Ye package FastAPI based voice + chat AI assistant hai.

## Phone par (Android + Termux)

1. Termux install karo (official source/F-Droid/GitHub release se).
2. Termux kholo aur run karo:

```bash
pkg update
pkg install python unzip
```

3. Is ZIP ko phone me extract karo aur project folder me jao.
4. Setup:

```bash
./setup.sh
```

5. `.env` me apni OpenAI API key aur strong APP_PASSWORD bharo.
6. Start:

```bash
./run.sh
```

7. Phone ke browser me kholo:

`http://127.0.0.1:8000`

## LAN par doosre device se access

```bash
./run-lan.sh
```

Phir same Wi-Fi wale device se phone ka local IP use karo:

`http://PHONE_IP:8000`

Public internet par bina HTTPS/reverse proxy ke expose mat karo.

## API endpoints

- `GET /health` — server status
- `GET /api/check` — access-code check
- `POST /api/chat` — text chat
- `POST /api/voice` — audio upload → transcript + AI reply + audio
- `POST /api/reset` — session memory reset
- `GET /docs` — FastAPI interactive API documentation

### `/api/chat` example

Header:

`X-Access-Code: YOUR_APP_PASSWORD`

JSON:

```json
{
  "text": "Delhi ka weather batao",
  "session_id": "my-phone"
}
```

## Important

- OpenAI API key required for AI/STT/TTS features.
- API usage can incur OpenAI charges.
- Lights and door lock are currently simulated in Python memory; they are NOT real hardware controls until an IoT controller is connected.
- Timer is browser-side.
- `.env` me secret key rakho; ise share/upload mat karo.
