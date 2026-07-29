"""
Webhook manager - creates webhooks and maps source → target.
"""
import asyncio
import logging
from typing import Callable, Optional

from .discord_client import DiscordClient

logger = logging.getLogger(__name__)


class WebhookManager:
    """Create webhooks in cloned channels and build the mapping."""

    def __init__(self, client: DiscordClient, progress_cb: Optional[Callable] = None):
        self.client = client
        self.progress_cb = progress_cb or (lambda msg, pct: None)

    async def setup_webhooks(
        self, channel_mapping: dict[str, dict]
    ) -> dict[str, dict]:
        """
        For every cloned channel (not category), create a webhook in both
        source and target channels and store the mapping.
        """
        text_channels = {
            cid: info
            for cid, info in channel_mapping.items()
            if info.get("type") in ("text", "announcement", "forum")
            and info.get("target_id") is not None
        }
        total = len(text_channels)
        if total == 0:
            self.progress_cb("No text channels to webhook...", 90)
            return channel_mapping

        done = 0
        for source_id, info in text_channels.items():
            target_id = info["target_id"]

            # Get source webhooks (or create one)
            try:
                source_webhooks = await self.client.get_channel_webhooks(source_id)
                if source_webhooks:
                    source_wh_url = f"https://discord.com/api/webhooks/{source_webhooks[0]['id']}/{source_webhooks[0]['token']}"
                else:
                    wh = await self.client.create_webhook(source_id, "CloneHook-Source")
                    source_wh_url = f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
                channel_mapping[source_id]["source_webhook_url"] = source_wh_url
            except Exception as e:
                logger.error(f"Source webhook for {info['source_name']}: {e}")
                channel_mapping[source_id]["source_webhook_url"] = f"ERROR: {e}"

            # Create webhook in target channel
            try:
                wh = await self.client.create_webhook(target_id, "CloneHook-Target")
                target_wh_url = f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
                channel_mapping[source_id]["target_webhook_url"] = target_wh_url
            except Exception as e:
                logger.error(f"Target webhook for {info['target_name']}: {e}")
                channel_mapping[source_id]["target_webhook_url"] = f"ERROR: {e}"

            done += 1
            self.progress_cb(
                f"Setting up webhooks... ({done}/{total})",
                80 + int(15 * done / total),
            )
            await asyncio.sleep(0.6)

        self.progress_cb("Webhooks setup complete!", 95)
        return channel_mapping
