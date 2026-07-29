# Discord Server Cloner

Desktop GUI tool to clone Discord server structure — categories, channels, webhooks — using your own account token via `discord.py-self`.

## Features

- **Token login via discord.py-self** — full Discord API support with built-in rate limiting & retry
- **Proxy support** — HTTP proxy (e.g. Clash/V2Ray `127.0.0.1:7897`), toggle on/off
- **Server structure cloning** — categories, text, voice, announcement, stage, forum channels
- **Webhook mapping** — creates webhooks on both source and target, ID ↔ URL mapping
- **Export** — JSON / CSV / Markdown, copy to clipboard or download file
- **Dark theme** — native PySide6 window, Discord-inspired palette

## Requirements

- Python 3.10+
- A Discord user token
- Manage Server permission on both source and target

## Quick Start

```bash
git clone https://github.com/ZRnown/discord-server-cloner.git
cd discord-server-cloner
pip install -r requirements.txt
python main.py
```

## Proxy

If you're behind a VPN/proxy (Clash, V2Ray, etc.), check **Use Proxy** and enter your proxy URL (default `http://127.0.0.1:7897`).  
Uncheck if you connect directly.

## How to Get Your Discord Token

1. Open Discord in browser, press `F12`
2. Network tab → find any `discord.com/api` request
3. Copy the `Authorization` header value

> Token never saved to disk, never sent anywhere except Discord API.

## Usage Flow

1. Paste token → check proxy settings → **Verify & Load Servers**
2. Pick source + target server → **Start Clone**
3. Watch real-time progress bar
4. Export the channel ↔ webhook mapping

## Tech Stack

| Layer | Technology |
|---|---|
| Discord API | `discord.py-self` |
| GUI | PySide6 (Qt 6) |
| Async | asyncio + QThread |

No browser automation. No Selenium.

## Disclaimer

Self-botting is against Discord ToS. Use at your own risk.

## License

MIT
