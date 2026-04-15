import os
import aiohttp
import asyncio
import time
from typing import Any, Optional, Literal
from dotenv import load_dotenv

from .cache import MySQLCache
from .endpoints import VoxylApiEndpoint

load_dotenv()


class VoxylAPI:
    def __init__(
        self,
        cache: MySQLCache,
        *,
        base_url: str = "https://api.voxyl.net",
        api_key: str = os.environ.get("API_KEY", ""),
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.cache = cache
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "VoxlyticsClient/1.0"},
            )

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _make_cache_key(self, endpoint: VoxylApiEndpoint, params: dict) -> str:
        return self.cache.make_key(endpoint.value, params)

    async def request(
        self, endpoint: VoxylApiEndpoint, *, ttl: int = 300, retries: int = 3, **params
    ) -> Any:

        await self.start()

        request_params = dict(params)
        request_params["api"] = self.api_key

        cache_key = self._make_cache_key(endpoint, params)

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/{endpoint.value.format(**params)}"

        last_error = None

        for attempt in range(retries):
            try:
                async with self.session.get(url, params=request_params) as resp:
                    text = await resp.text()

                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except Exception:
                            data = text

                        self.cache.set(cache_key, endpoint.value, data, ttl)
                        return data

                    if resp.status == 429:
                        await asyncio.sleep(2**attempt)
                        continue

                    return {"error": resp.status, "data": text}

            except Exception as e:
                last_error = e
                await asyncio.sleep(2**attempt)

        return {"error": "request_failed", "detail": str(last_error)}


SkinStyle = Literal[
    "face",
    "front",
    "frontfull",
    "head",
    "bust",
    "full",
    "skin",
    "processedskin",
]

DEFAULT_STEVE_SKIN_URL = (
    "https://textures.minecraft.net/texture/"
    "a4665d6a9c07b7b3ecf3b9f4b1c6bff0e43a9a3b65e5b4b94a3a4567d9a12345"
)


class SkinAPI:
    def __init__(self, cache: MySQLCache):
        self.cache = cache
        self.session: aiohttp.ClientSession | None = None

    async def start(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5),
                headers={"User-Agent": "Voxyl Client"},
            )

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _make_key(self, uuid: str, style: SkinStyle) -> str:
        return self.cache.make_key(
            "skin_model",
            {"uuid": uuid, "style": style},
        )

    async def fetch_skin_model(
        self,
        uuid: str,
        style: SkinStyle = "full",
    ) -> bytes:
        await self.start()

        cache_key = self._make_key(uuid, style)

        cached = self.cache.get(cache_key)
        if cached is not None:
            return bytes(cached)

        base_url = "https://visage.surgeplay.com"
        url = f"{base_url}/{style}/256/{uuid}"

        headers = {"User-Agent": "Voxyl Client"}

        try:
            async with self.session.get(url, headers=headers) as res:
                if res.status == 200:
                    data = await res.read()

                    self.cache.set(
                        cache_key,
                        "skin_model",
                        list(data),
                        ttl=3600,
                    )

                    return data

                raise Exception(f"Skin fetch failed with status {res.status}")

        except Exception:
            async with self.session.get(DEFAULT_STEVE_SKIN_URL, headers=headers) as res:
                data = await res.read()

                self.cache.set(
                    cache_key,
                    "skin_model_fallback",
                    list(data),
                    ttl=3600,
                )

                return data


cache = MySQLCache(default_ttl=300)
API = VoxylAPI(cache=cache)
SKINS_API = SkinAPI(cache=cache)
