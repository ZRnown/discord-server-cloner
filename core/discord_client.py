"""
Discord HTTP API client for self-bot operations.
Uses raw Discord REST API with aiohttp (user token).
"""
import asyncio
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://discord.com/api/v10"


class DiscordClient:
    """Async Discord HTTP client using a user token."""

    def __init__(self, token: str):
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
        self._user_info: Optional[dict] = None

    @property
    def headers(self) -> dict:
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, path: str, **kwargs) -> dict | list | None:
        """Make an API request. Returns parsed JSON or None."""
        url = f"{BASE_URL}{path}"
        async with self.session.request(method, url, **kwargs) as resp:
            if resp.status == 429:
                retry_after = (await resp.json()).get("retry_after", 5)
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._request(method, path, **kwargs)
            if resp.status == 204:
                return None
            data = await resp.json()
            if resp.status >= 400:
                raise DiscordAPIError(resp.status, data)
            return data

    # ── User ──

    async def get_me(self) -> dict:
        """Verify token and return user info."""
        if self._user_info is None:
            self._user_info = await self._request("GET", "/users/@me")
        return self._user_info

    # ── Guilds ──

    async def get_my_guilds(self) -> list[dict]:
        """Get all guilds the user is in."""
        return await self._request("GET", "/users/@me/guilds")

    async def get_guild(self, guild_id: str) -> dict:
        """Get a single guild."""
        return await self._request("GET", f"/guilds/{guild_id}")

    async def get_guild_channels(self, guild_id: str) -> list[dict]:
        """Get all channels in a guild."""
        return await self._request("GET", f"/guilds/{guild_id}/channels")

    # ── Channels ──

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        channel_type: int = 0,
        parent_id: Optional[str] = None,
        position: Optional[int] = None,
        topic: Optional[str] = None,
        nsfw: bool = False,
        rate_limit_per_user: Optional[int] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
    ) -> dict:
        """Create a channel in a guild.

        channel_type: 0=text, 2=voice, 4=category
        """
        payload = {"name": name, "type": channel_type}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        if position is not None:
            payload["position"] = position
        if topic is not None:
            payload["topic"] = topic
        if nsfw:
            payload["nsfw"] = True
        if rate_limit_per_user is not None:
            payload["rate_limit_per_user"] = rate_limit_per_user
        if bitrate is not None:
            payload["bitrate"] = bitrate
        if user_limit is not None:
            payload["user_limit"] = user_limit

        return await self._request("POST", f"/guilds/{guild_id}/channels", json=payload)

    # ── Webhooks ──

    async def create_webhook(self, channel_id: str, name: str = "CloneHook") -> dict:
        """Create a webhook in a channel."""
        return await self._request(
            "POST", f"/channels/{channel_id}/webhooks", json={"name": name}
        )

    async def get_channel_webhooks(self, channel_id: str) -> list[dict]:
        """Get all webhooks in a channel."""
        return await self._request("GET", f"/channels/{channel_id}/webhooks")


class DiscordAPIError(Exception):
    def __init__(self, status: int, data: dict):
        self.status = status
        self.data = data
        super().__init__(f"Discord API error {status}: {data.get('message', 'unknown')}")
