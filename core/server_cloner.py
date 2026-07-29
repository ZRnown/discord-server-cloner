"""
Server structure cloning logic — uses discord.py-self guild objects.
"""
import asyncio
import logging
from typing import Callable, Optional

import discord
from .discord_client import DiscordSelfClient

logger = logging.getLogger(__name__)

CHILD_TYPES = {
    discord.ChannelType.text: "text",
    discord.ChannelType.voice: "voice",
    discord.ChannelType.news: "announcement",
    discord.ChannelType.stage_voice: "stage",
    discord.ChannelType.forum: "forum",
}


class ServerCloner:
    """Clone categories + channels from source guild to target guild."""

    def __init__(self, client: DiscordSelfClient, progress_cb: Optional[Callable] = None):
        self.client = client
        self.progress_cb = progress_cb or (lambda msg, pct: None)
        self.mapping: dict[int, dict] = {}

    async def clone(self, source_guild_id: int, target_guild_id: int) -> dict[int, dict]:
        self.progress_cb("Fetching source channels...", 5)
        channels = await self.client.get_guild_channels(source_guild_id)
        if not channels:
            self.progress_cb("No channels found in source server!", 100)
            return {}

        # Separate categories and children
        categories = [c for c in channels if isinstance(c, discord.CategoryChannel)]
        children_by_parent: dict[int, list[discord.abc.GuildChannel]] = {}
        orphans: list[discord.abc.GuildChannel] = []

        for c in channels:
            if isinstance(c, discord.CategoryChannel):
                continue
            if c.type not in CHILD_TYPES:
                continue
            pid = getattr(c, "category_id", None) or (c.category.id if c.category else None)
            if pid:
                children_by_parent.setdefault(pid, []).append(c)
            else:
                orphans.append(c)

        total = len(channels)
        done = 0
        cat_map: dict[int, int] = {}

        # 1. Clone categories
        self.progress_cb(f"Cloning {len(categories)} categories...", 10)
        for cat in sorted(categories, key=lambda c: c.position):
            try:
                new_cat = await self.client.create_category(
                    target_guild_id, cat.name, position=cat.position
                )
                cat_map[cat.id] = new_cat.id
                self.mapping[cat.id] = {
                    "source_id": str(cat.id),
                    "source_name": cat.name,
                    "target_id": str(new_cat.id),
                    "target_name": new_cat.name,
                    "type": "category",
                    "webhook_url": None,
                }
                done += 1
            except Exception as e:
                logger.error(f"Failed to clone category {cat.name}: {e}")
                self.mapping[cat.id] = {
                    "source_id": str(cat.id),
                    "source_name": cat.name,
                    "target_id": None,
                    "target_name": None,
                    "type": "category",
                    "webhook_url": None,
                    "error": str(e),
                }
            self.progress_cb(
                f"Cloning categories... ({done}/{len(categories)})",
                10 + int(20 * done / total),
            )
            await asyncio.sleep(0.6)

        # 2. Clone channels inside categories
        self.progress_cb("Cloning channels...", 30)
        for parent_id, children in children_by_parent.items():
            target_parent_id = cat_map.get(parent_id)
            if not target_parent_id:
                logger.warning(f"No target category for {parent_id}, skipping child channels")
                done += len(children)
                continue
            for ch in sorted(children, key=lambda c: c.position):
                try:
                    new_ch = await self._clone_channel(ch, target_guild_id, target_parent_id)
                    self._record_mapping(ch, new_ch)
                    done += 1
                except Exception as e:
                    logger.error(f"Failed to clone channel {ch.name}: {e}")
                    self.mapping[ch.id] = self._error_entry(ch, str(e))
                    done += 1
                self.progress_cb(
                    f"Cloning channels... ({done}/{total})",
                    30 + int(30 * done / total),
                )
                await asyncio.sleep(0.6)

        # 3. Clone orphans
        self.progress_cb("Cloning orphan channels...", 60)
        for ch in sorted(orphans, key=lambda c: c.position):
            try:
                new_ch = await self._clone_channel(ch, target_guild_id, None)
                self._record_mapping(ch, new_ch)
                done += 1
            except Exception as e:
                logger.error(f"Failed to clone orphan channel {ch.name}: {e}")
                self.mapping[ch.id] = self._error_entry(ch, str(e))
                done += 1
            self.progress_cb(
                f"Cloning channels... ({done}/{total})",
                60 + int(20 * done / total),
            )
            await asyncio.sleep(0.6)

        self.progress_cb(f"Cloned {done}/{total} channels", 80)
        return self.mapping

    async def _clone_channel(
        self,
        ch: discord.abc.GuildChannel,
        target_guild_id: int,
        target_parent_id: Optional[int],
    ) -> discord.abc.GuildChannel:
        ch_type = ch.type
        if ch_type == discord.ChannelType.text:
            slowmode = getattr(ch, "slowmode_delay", 0) or 0
            return await self.client.create_text_channel(
                target_guild_id, ch.name,
                parent_id=target_parent_id, position=ch.position,
                topic=getattr(ch, "topic", None),
                nsfw=getattr(ch, "nsfw", False),
                slowmode_delay=slowmode if slowmode > 0 else None,
            )
        elif ch_type == discord.ChannelType.news:
            slowmode = getattr(ch, "slowmode_delay", 0) or 0
            return await self.client.create_text_channel(
                target_guild_id, ch.name,
                parent_id=target_parent_id, position=ch.position,
                topic=getattr(ch, "topic", None),
                nsfw=getattr(ch, "nsfw", False),
                slowmode_delay=slowmode if slowmode > 0 else None,
            )
        elif ch_type == discord.ChannelType.voice:
            return await self.client.create_voice_channel(
                target_guild_id, ch.name,
                parent_id=target_parent_id, position=ch.position,
                bitrate=getattr(ch, "bitrate", None),
                user_limit=getattr(ch, "user_limit", None),
            )
        elif ch_type == discord.ChannelType.stage_voice:
            return await self.client.create_stage_channel(
                target_guild_id, ch.name,
                parent_id=target_parent_id, position=ch.position,
                bitrate=getattr(ch, "bitrate", None),
            )
        elif ch_type == discord.ChannelType.forum:
            return await self.client.create_forum_channel(
                target_guild_id, ch.name,
                parent_id=target_parent_id, position=ch.position,
                topic=getattr(ch, "topic", None),
                nsfw=getattr(ch, "nsfw", False),
            )
        raise ValueError(f"Unsupported channel type: {ch_type}")

    def _record_mapping(self, src: discord.abc.GuildChannel, tgt: discord.abc.GuildChannel):
        self.mapping[src.id] = {
            "source_id": str(src.id),
            "source_name": src.name,
            "target_id": str(tgt.id),
            "target_name": tgt.name,
            "type": CHILD_TYPES.get(src.type, str(src.type)),
            "webhook_url": None,
        }

    def _error_entry(self, ch: discord.abc.GuildChannel, error: str) -> dict:
        return {
            "source_id": str(ch.id),
            "source_name": ch.name,
            "target_id": None,
            "target_name": None,
            "type": CHILD_TYPES.get(ch.type, str(ch.type)),
            "webhook_url": None,
            "error": error,
        }
