"""
Webhook manager — creates webhooks and maps source → target.
"""
import asyncio
import logging
from typing import Callable, Optional

from .discord_client import DiscordSelfClient

logger = logging.getLogger(__name__)


WEBHOOK_CHANNEL_TYPES = {"text", "announcement", "forum"}


class WebhookManager:
    """Create webhooks in cloned channels and build the mapping."""

    def __init__(self, client: DiscordSelfClient, progress_cb: Optional[Callable] = None):
        self.client = client
        self.progress_cb = progress_cb or (lambda msg, pct: None)

    async def setup_webhooks(self, channel_mapping: dict[int, dict]) -> dict[int, dict]:
        """For every text-capable cloned channel, create webhooks on both sides."""
        text_entries = {
            cid: info
            for cid, info in channel_mapping.items()
            if info.get("type") in WEBHOOK_CHANNEL_TYPES and info.get("target_id") is not None
        }
        total = len(text_entries)
        if total == 0:
            self.progress_cb("没有需要设置 Webhook 的频道...", 90)
            return channel_mapping

        done = 0
        for source_id, info in text_entries.items():
            target_id = info["target_id"]

            # Source webhook
            try:
                source_whs = await self.client.get_channel_webhooks(int(source_id))
                if source_whs:
                    wh = source_whs[0]
                    info["source_webhook_url"] = (
                        f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
                    )
                else:
                    wh = await self.client.create_webhook(int(source_id), "CloneHook-Source")
                    info["source_webhook_url"] = (
                        f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
                    )
            except Exception as e:
                logger.error(f"Source webhook for {info['source_name']}: {e}")
                info["source_webhook_url"] = f"ERROR: {e}"

            # Target webhook
            try:
                wh = await self.client.create_webhook(int(target_id), "CloneHook-Target")
                info["target_webhook_url"] = (
                    f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
                )
            except Exception as e:
                logger.error(f"Target webhook for {info['target_name']}: {e}")
                info["target_webhook_url"] = f"ERROR: {e}"

            done += 1
            self.progress_cb(
                f"正在设置 Webhook... ({done}/{total})",
                80 + int(15 * done / total),
            )
            await asyncio.sleep(0.6)

        self.progress_cb("Webhook 设置完成！", 95)
        return channel_mapping
