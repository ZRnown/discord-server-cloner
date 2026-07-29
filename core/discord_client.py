"""
Discord self-bot client wrapper — uses discord.py-self with proxy support.
"""
import asyncio
import logging
from typing import Optional

import discord

logger = logging.getLogger(__name__)


class DiscordSelfClient:
    """Async Discord self-bot client using discord.py-self."""

    def __init__(self, token: str, proxy: Optional[str] = None):
        self.token = token
        self.proxy = proxy  # e.g. "http://127.0.0.1:7897"
        self.client: Optional[discord.Client] = None

    async def __aenter__(self):
        kwargs = {}
        if self.proxy:
            kwargs["proxy"] = self.proxy
        self.client = discord.Client(**kwargs)
        await self.client.login(self.token)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.close()

    # ── User ──

    @property
    def user(self):
        return self.client.user

    # ── Guilds ──

    async def get_manageable_guilds(self) -> list[discord.Guild]:
        """Get all guilds the user belongs to."""
        return await self.client.fetch_guilds()

    # ── Channels ──

    async def get_guild_channels(self, guild_id: int) -> list[discord.abc.GuildChannel]:
        """Fetch all channels in a guild."""
        guild = await self.client.fetch_guild(guild_id)
        return await guild.fetch_channels()

    async def create_category(
        self, guild_id: int, name: str, position: Optional[int] = None
    ) -> discord.CategoryChannel:
        guild = await self.client.fetch_guild(guild_id)
        return await guild.create_category_channel(name, position=position or 0)

    async def create_text_channel(
        self,
        guild_id: int,
        name: str,
        *,
        parent_id: Optional[int] = None,
        position: Optional[int] = None,
        topic: Optional[str] = None,
        nsfw: bool = False,
        slowmode_delay: Optional[int] = None,
    ) -> discord.TextChannel:
        guild = await self.client.fetch_guild(guild_id)
        parent = await self._resolve_parent(guild, parent_id)
        return await guild.create_text_channel(
            name,
            category=parent,
            position=position or 0,
            topic=topic,
            nsfw=nsfw,
            slowmode_delay=slowmode_delay or 0,
        )

    async def create_voice_channel(
        self,
        guild_id: int,
        name: str,
        *,
        parent_id: Optional[int] = None,
        position: Optional[int] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
    ) -> discord.VoiceChannel:
        guild = await self.client.fetch_guild(guild_id)
        parent = await self._resolve_parent(guild, parent_id)
        return await guild.create_voice_channel(
            name,
            category=parent,
            position=position or 0,
            bitrate=bitrate,
            user_limit=user_limit or 0,
        )

    async def create_forum_channel(
        self,
        guild_id: int,
        name: str,
        *,
        parent_id: Optional[int] = None,
        position: Optional[int] = None,
        topic: Optional[str] = None,
        nsfw: bool = False,
    ) -> discord.ForumChannel:
        guild = await self.client.fetch_guild(guild_id)
        parent = await self._resolve_parent(guild, parent_id)
        return await guild.create_forum_channel(
            name,
            category=parent,
            position=position or 0,
            topic=topic,
            nsfw=nsfw,
        )

    async def create_stage_channel(
        self,
        guild_id: int,
        name: str,
        *,
        parent_id: Optional[int] = None,
        position: Optional[int] = None,
        bitrate: Optional[int] = None,
    ) -> discord.StageChannel:
        guild = await self.client.fetch_guild(guild_id)
        parent = await self._resolve_parent(guild, parent_id)
        return await guild.create_stage_channel(
            name,
            category=parent,
            position=position or 0,
            bitrate=bitrate,
        )

    async def _resolve_parent(
        self, guild: discord.Guild, parent_id: Optional[int]
    ) -> Optional[discord.CategoryChannel]:
        if parent_id is None:
            return None
        for cat in guild.categories:
            if cat.id == parent_id:
                return cat
        return None

    # ── Webhooks ──

    async def create_webhook(self, channel_id: int, name: str = "CloneHook") -> discord.Webhook:
        """Create a webhook in a text-capable channel."""
        return await self.client.http.create_webhook(channel_id, name=name)

    async def get_channel_webhooks(self, channel_id: int) -> list[dict]:
        """Get all webhooks in a channel (returns raw dicts)."""
        return await self.client.http.channel_webhooks(channel_id)
