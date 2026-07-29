# Discord Server Cloner

A **desktop GUI** tool to clone Discord server structure using your own account token.  
Clone categories, channels, and create webhook mappings between source and target servers — all with a native Qt dark-theme interface.

## Features

- **Token-based login** — uses your Discord user token (never saved to disk, never leaves your machine)
- **Server structure cloning** — copies categories, text/voice/announcement/stage/forum channels, positions, topics, NSFW flags, slowmode, bitrate, user limits
- **Webhook mapping** — creates webhooks in every text-capable channel on both source and target, with full ID ↔ URL mapping
- **Export** — copy or download the channel ↔ webhook mapping as JSON / CSV / Markdown
- **Real-time progress** — live progress bar during clone
- **Dark theme** — native PySide6 (Qt) desktop window, Discord-inspired palette

## Screenshots

*(coming soon)*

## Requirements

- Python 3.10+
- PySide6
- aiohttp
- A Discord user token (see [How to get your token](#how-to-get-your-discord-token))
- You must have **Manage Server** permission on BOTH source and target servers

## Quick Start

```bash
# Clone the repo
git clone https://github.com/ZRnown/discord-server-cloner.git
cd discord-server-cloner

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

A native desktop window opens — no browser needed.

## How to Get Your Discord Token

> **Security warning**: Your token grants full access to your Discord account.  
> Never share it, and only paste it into tools you trust. This tool does NOT save or transmit your token.

1. Open Discord in your browser or desktop app
2. Press `F12` to open Developer Tools (`Ctrl+Shift+I`)
3. Go to the **Network** tab
4. Type any message or refresh the page
5. Find a request to `discord.com/api` — click it
6. Under **Request Headers**, find `Authorization`
7. Copy the value (long string, often starts with `mfa.` or ends with base64)

## Usage Flow

1. **Step 1** — Paste Discord token and click **Verify & Load Servers**
2. **Step 2** — Pick a **source** and **target** server from the dropdowns → click **Start Clone**
3. **Step 3** — Watch real-time progress
4. **Step 4** — Review results table, right-click rows to copy, or use the export buttons

## Output Mapping Format

| Field | Description |
|---|---|
| `source_channel_id` | Discord channel ID from the source server |
| `source_channel_name` | Channel name on source |
| `source_webhook_url` | Webhook URL created on source channel |
| `target_channel_id` | Discord channel ID on the target server |
| `target_channel_name` | Channel name on target |
| `target_webhook_url` | Webhook URL created on target channel |
| `channel_type` | `text`, `voice`, `announcement`, `forum`, `stage`, or `category` |
| `error` | Error message if cloning this channel failed (`null` if OK) |

## Tech Stack

| Layer | Technology |
|---|---|
| GUI | PySide6 (Qt 6) |
| Discord API | aiohttp → REST v10 |
| Async | asyncio + QThread |

No `discord.py`, no Selenium, no browser automation — pure HTTP REST API calls.

## Project Structure

```
discord-server-cloner/
├── main.py                      # Entry point
├── requirements.txt             # PySide6, aiohttp
├── core/
│   ├── discord_client.py        # Async HTTP client for Discord REST API v10
│   ├── server_cloner.py         # Category + channel cloning logic
│   ├── webhook_manager.py       # Webhook creation + mapping builder
│   └── mapping_exporter.py      # JSON / CSV / Markdown export
└── gui/
    ├── app.py                   # PySide6 desktop window (dark theme)
    └── __init__.py
```

## Disclaimer

This tool is a **self-bot** — it uses a Discord user token to automate actions via the REST API.  
Self-botting is technically against Discord's Terms of Service. Use responsibly and at your own risk.

## License

MIT
