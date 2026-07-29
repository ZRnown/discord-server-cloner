# Discord Server Cloner

A desktop GUI tool to clone Discord server structure using your own account token.  
Clone categories, channels, and create webhook mappings between source and target servers — all with a modern web-based interface.

## Features

- **Token-based login** — uses your Discord user token (never saved to disk)
- **Server structure cloning** — copies categories, text/voice/announcement/forum channels, positions, topics, NSFW flags, slowmode
- **Webhook mapping** — creates webhooks in every text-capable channel on both source and target, with full ID ↔ URL mapping
- **Export** — export the channel ↔ webhook mapping as JSON, CSV, or Markdown
- **Real-time progress** — WebSocket-powered live progress bar
- **Dark theme GUI** — clean web-based interface

## Screenshots

![Step 1 - Token](screenshots/step1.png)
![Step 2 - Server Select](screenshots/step2.png)
![Step 3 - Progress](screenshots/step3.png)
![Step 4 - Results](screenshots/step4.png)

## Requirements

- Python 3.10+
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

The GUI opens automatically at `http://127.0.0.1:5000`.

## How to Get Your Discord Token

> ⚠️ **Security warning**: Your token grants full access to your Discord account.  
> Never share it, and only paste it into tools you trust. This tool does NOT save or transmit your token.

1. Open Discord in your browser or desktop app
2. Press `F12` to open Developer Tools (or `Ctrl+Shift+I`)
3. Go to the **Network** tab
4. Type any message in a channel (don't send) or refresh the page
5. Look for a request to `discord.com/api` — click it
6. Under **Request Headers**, find `Authorization`
7. Copy the value (it's a long string — usually starts with `mfa.` or ends with base64)

## Usage Flow

1. **Step 1** — Paste your Discord token and click "Verify & Load Servers"
2. **Step 2** — Select a **source server** (the one you want to copy) and a **target server** (where to create the clone)
3. **Step 3** — Click "Start Clone" and watch the real-time progress
4. **Step 4** — Review the results table, copy to clipboard, or download as JSON/CSV/Markdown

## Output Mapping Format

Each entry in the exported mapping contains:

| Field | Description |
|---|---|
| `source_channel_id` | Discord channel ID from the source server |
| `source_channel_name` | Channel name on source |
| `source_webhook_url` | Webhook URL created on source channel |
| `target_channel_id` | Discord channel ID on the target server |
| `target_channel_name` | Channel name on target |
| `target_webhook_url` | Webhook URL created on target channel |
| `channel_type` | `text`, `voice`, `announcement`, `forum`, or `category` |
| `error` | Error message if cloning this channel failed (null if OK) |

## Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, aiohttp
- **Frontend**: Vanilla HTML/CSS/JS with Socket.IO client
- **Discord API**: Direct HTTP REST API (v10)

## Disclaimer

This tool is a **self-bot** — it uses a user token to automate actions on Discord.  
Self-botting is technically against Discord's Terms of Service. Use responsibly and at your own risk.

## License

MIT
