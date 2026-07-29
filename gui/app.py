"""
Flask web GUI for the Discord Server Cloner.
Socket.IO provides real-time progress to the frontend.
"""
import asyncio
import json
import logging
import threading
import sys
import os

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.discord_client import DiscordClient, DiscordAPIError
from core.server_cloner import ServerCloner
from core.webhook_manager import WebhookManager
from core.mapping_exporter import export_mapping

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "discord-cloner-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*")

# Per-session state (in-memory only)
session_state = {
    "token": None,
    "mapping": None,
    "running": False,
}


def emit_progress(msg: str, pct: int):
    """Send progress to frontend via WebSocket."""
    socketio.emit("progress", {"message": msg, "percent": pct})


async def run_clone(token: str, source_id: str, target_id: str):
    """Run the full clone pipeline."""
    try:
        async with DiscordClient(token) as client:
            emit_progress("Verifying token...", 0)
            user = await client.get_me()
            emit_progress(f"Logged in as {user['username']}#{user['discriminator']}", 5)

            # Clone structure
            cloner = ServerCloner(client, progress_cb=emit_progress)
            mapping = await cloner.clone(source_id, target_id)

            # Set up webhooks
            wh_manager = WebhookManager(client, progress_cb=emit_progress)
            mapping = await wh_manager.setup_webhooks(mapping)

            session_state["mapping"] = mapping
            emit_progress("Done! All channels cloned and webhooks created.", 100)
            socketio.emit("clone_complete", {"mapping": mapping})
    except DiscordAPIError as e:
        emit_progress(f"Discord API Error: {e}", 100)
        socketio.emit("clone_error", {"error": str(e)})
    except Exception as e:
        logger.exception("Clone failed")
        emit_progress(f"Error: {e}", 100)
        socketio.emit("clone_error", {"error": str(e)})
    finally:
        session_state["running"] = False


# ── Routes ──


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """Verify a Discord token and return user info + guilds."""
    data = request.get_json()
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "No token provided"}), 400

    async def _verify():
        async with DiscordClient(token) as client:
            user = await client.get_me()
            guilds = await client.get_my_guilds()
            # Filter guilds where user has MANAGE_GUILD or is owner
            manageable = [
                g for g in guilds
                if (g.get("owner", False))
                or (int(g.get("permissions", 0)) & 0x20)  # MANAGE_GUILD
            ]
            return user, manageable

    try:
        loop = asyncio.new_event_loop()
        user, guilds = loop.run_until_complete(_verify())
        loop.close()
        session_state["token"] = token
        return jsonify({
            "ok": True,
            "user": f"{user['username']}#{user['discriminator']}",
            "guilds": [
                {"id": g["id"], "name": g["name"], "icon": g.get("icon")}
                for g in guilds
            ],
        })
    except DiscordAPIError as e:
        return jsonify({"ok": False, "error": str(e)}), 401
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/clone", methods=["POST"])
def api_clone():
    """Start the clone operation."""
    if session_state.get("running"):
        return jsonify({"ok": False, "error": "Already running"}), 409

    data = request.get_json()
    token = data.get("token", session_state.get("token", ""))
    source_id = data.get("source_id", "").strip()
    target_id = data.get("target_id", "").strip()

    if not token:
        return jsonify({"ok": False, "error": "No token provided"}), 400
    if not source_id or not target_id:
        return jsonify({"ok": False, "error": "Source and target server IDs required"}), 400
    if source_id == target_id:
        return jsonify({"ok": False, "error": "Source and target must be different"}), 400

    session_state["running"] = True

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_clone(token, source_id, target_id))
        loop.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"ok": True, "message": "Clone started"})


@app.route("/api/export", methods=["GET"])
def api_export():
    """Export the mapping in the requested format."""
    fmt = request.args.get("format", "json")
    mapping = session_state.get("mapping")
    if not mapping:
        return jsonify({"ok": False, "error": "No mapping available"}), 404
    exported = export_mapping(mapping, fmt)
    return jsonify({"ok": True, "data": exported, "format": fmt})


@app.route("/api/export/download", methods=["GET"])
def api_export_download():
    """Download the mapping as a file."""
    fmt = request.args.get("format", "json")
    mapping = session_state.get("mapping")
    if not mapping:
        return "No mapping available", 404
    exported = export_mapping(mapping, fmt)
    mimetypes = {"json": "application/json", "csv": "text/csv", "markdown": "text/markdown"}
    return send_file(
        io.BytesIO(exported.encode("utf-8")),
        mimetype=mimetypes.get(fmt, "application/octet-stream"),
        as_attachment=True,
        download_name=f"discord-channel-mapping.{fmt if fmt != 'markdown' else 'md'}",
    )


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({"running": session_state.get("running", False)})


# ── Socket.IO ──


@socketio.on("connect")
def on_connect():
    emit("connected", {"status": "ok"})


def main():
    import webbrowser
    port = 5000
    print(f"\n  Discord Server Cloner GUI\n  Opening http://127.0.0.1:{port}\n")
    webbrowser.open(f"http://127.0.0.1:{port}")
    socketio.run(app, host="127.0.0.1", port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
