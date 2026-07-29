"""
Server structure cloning logic.
Clones categories and channels from source guild to target guild.
"""
import asyncio
import logging
from typing import Callable, Optional

from .discord_client import DiscordClient

logger = logging.getLogger(__name__)

# Channel type constants
CHANNEL_TEXT = 0
CHANNEL_VOICE = 2
CHANNEL_CATEGORY = 4
CHANNEL_ANNOUNCEMENT = 5
CHANNEL_STAGE = 13
CHANNEL_FORUM = 15

# Channel types that go inside categories (not categories themselves)
CHILD_TYPES = {
    CHANNEL_TEXT: "text",
    CHANNEL_VOICE: "voice",
    CHANNEL_ANNOUNCEMENT: "announcement",
    CHANNEL_STAGE: "stage",
    CHANNEL_FORUM: "forum",
}


class ServerCloner:
    """Clone server structure from source to target guild."""

    def __init__(self, client: DiscordClient, progress_cb: Optional[Callable] = None):
        self.client = client
        self.progress_cb = progress_cb or (lambda msg, pct: None)
        # Mapping: {source_channel_id: {source, target, webhook_url}}
        self.mapping: dict[str, dict] = {}

    async def clone(
        self, source_guild_id: str, target_guild_id: str
    ) -> dict[str, dict]:
        """Clone server structure. Returns channel mapping."""
        self.progress_cb("Fetching source channels...", 5)
        source_channels = await self.client.get_guild_channels(source_guild_id)

        if not source_channels:
            self.progress_cb("No channels found in source server!", 100)
            return {}

        # Build hierarchy: categories first, then their children, then orphans
        categories = [
            c for c in source_channels if c["type"] == CHANNEL_CATEGORY
        ]
        orphans = [
            c
            for c in source_channels
            if c["type"] in CHILD_TYPES and not c.get("parent_id")
        ]
        children_by_parent: dict[str, list[dict]] = {}
        for c in source_channels:
            if c["type"] in CHILD_TYPES and c.get("parent_id"):
                children_by_parent.setdefault(c["parent_id"], []).append(c)

        total = len(source_channels)
        done = 0

        # Track category mapping: source_id → target_id
        cat_map: dict[str, str] = {}

        self.progress_cb(f"Cloning {len(categories)} categories...", 10)

        # 1. Clone categories
        for cat in sorted(categories, key=lambda c: c.get("position", 0)):
            try:
                new_cat = await self.client.create_channel(
                    guild_id=target_guild_id,
                    name=cat["name"],
                    channel_type=CHANNEL_CATEGORY,
                    position=cat.get("position"),
                )
                cat_map[cat["id"]] = new_cat["id"]
                self.mapping[cat["id"]] = {
                    "source_id": cat["id"],
                    "source_name": cat["name"],
                    "target_id": new_cat["id"],
                    "target_name": new_cat["name"],
                    "type": "category",
                    "webhook_url": None,
                }
                done += 1
            except Exception as e:
                logger.error(f"Failed to clone category {cat['name']}: {e}")
                self.mapping[cat["id"]] = {
                    "source_id": cat["id"],
                    "source_name": cat["name"],
                    "target_id": None,
                    "target_name": None,
                    "type": "category",
                    "webhook_url": None,
                    "error": str(e),
                }
            self.progress_cb(
                f"Cloning categories... ({done}/{len(categories)})", 10 + int(20 * done / total)
            )
            await asyncio.sleep(0.5)  # Rate limit safety

        # 2. Clone channels inside categories
        self.progress_cb("Cloning channels inside categories...", 30)
        for parent_id, children in children_by_parent.items():
            target_parent_id = cat_map.get(parent_id)
            if not target_parent_id:
                logger.warning(f"No target category for source parent {parent_id}, skipping child channels")
                done += len(children)
                continue
            for ch in sorted(children, key=lambda c: c.get("position", 0)):
                try:
                    ch_type = ch["type"]
                    if ch_type not in CHILD_TYPES:
                        continue
                    new_ch = await self.client.create_channel(
                        guild_id=target_guild_id,
                        name=ch["name"],
                        channel_type=ch_type,
                        parent_id=target_parent_id,
                        position=ch.get("position"),
                        topic=ch.get("topic", ""),
                        nsfw=ch.get("nsfw", False),
                        rate_limit_per_user=ch.get("rate_limit_per_user", 0) or None,
                        bitrate=ch.get("bitrate"),
                        user_limit=ch.get("user_limit"),
                    )
                    self.mapping[ch["id"]] = {
                        "source_id": ch["id"],
                        "source_name": ch["name"],
                        "target_id": new_ch["id"],
                        "target_name": new_ch["name"],
                        "type": CHILD_TYPES[ch_type],
                        "webhook_url": None,
                    }
                    done += 1
                except Exception as e:
                    logger.error(f"Failed to clone channel {ch['name']}: {e}")
                    self.mapping[ch["id"]] = {
                        "source_id": ch["id"],
                        "source_name": ch["name"],
                        "target_id": None,
                        "target_name": None,
                        "type": CHILD_TYPES.get(ch["type"], "unknown"),
                        "webhook_url": None,
                        "error": str(e),
                    }
                    done += 1
                self.progress_cb(
                    f"Cloning channels... ({done}/{total})", 30 + int(30 * done / total)
                )
                await asyncio.sleep(0.5)

        # 3. Clone orphan channels (no category)
        self.progress_cb("Cloning orphan channels...", 60)
        for ch in sorted(orphans, key=lambda c: c.get("position", 0)):
            try:
                ch_type = ch["type"]
                if ch_type not in CHILD_TYPES:
                    continue
                new_ch = await self.client.create_channel(
                    guild_id=target_guild_id,
                    name=ch["name"],
                    channel_type=ch_type,
                    position=ch.get("position"),
                    topic=ch.get("topic", ""),
                    nsfw=ch.get("nsfw", False),
                    rate_limit_per_user=ch.get("rate_limit_per_user", 0) or None,
                    bitrate=ch.get("bitrate"),
                    user_limit=ch.get("user_limit"),
                )
                self.mapping[ch["id"]] = {
                    "source_id": ch["id"],
                    "source_name": ch["name"],
                    "target_id": new_ch["id"],
                    "target_name": new_ch["name"],
                    "type": CHILD_TYPES[ch_type],
                    "webhook_url": None,
                }
                done += 1
            except Exception as e:
                logger.error(f"Failed to clone orphan channel {ch['name']}: {e}")
                self.mapping[ch["id"]] = {
                    "source_id": ch["id"],
                    "source_name": ch["name"],
                    "target_id": None,
                    "target_name": None,
                    "type": CHILD_TYPES.get(ch["type"], "unknown"),
                    "webhook_url": None,
                    "error": str(e),
                }
                done += 1
            self.progress_cb(
                f"Cloning channels... ({done}/{total})", 60 + int(20 * done / total)
            )
            await asyncio.sleep(0.5)

        self.progress_cb(f"Cloned {done}/{total} channels", 80)
        return self.mapping
