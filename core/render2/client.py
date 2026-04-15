import os
import json
import hashlib
from abc import ABC, abstractmethod
from io import BytesIO

from dotenv import load_dotenv

from aiohttp import ClientSession, ClientTimeout, FormData
from cachetools import TTLCache
from cachetools_async import cached

from .placeholders import PlaceholderValues

load_dotenv()


_cache = TTLCache(maxsize=128, ttl=300)

class RenderingClient(ABC):
    def __init__(self, route: str) -> None:
        self._route = route

    async def _make_request(self, formdata: FormData) -> bytes:
        async with ClientSession(timeout=ClientTimeout(total=10)) as session:
            res = await session.post(
                f"{os.environ.get('RENDERER_HOSTNAME')}{self._route}",
                data=formdata,
            )
            res.raise_for_status()
            return await res.content.read()


    async def _make_request_cached(self, cache_key: str, payload: str) -> bytes:
        if cache_key in _cache:
            return _cache[cache_key]

        form = FormData()
        form.add_field(
            "placeholder_values",
            payload.encode("utf-8"),
            filename="blob",
            content_type="application/json",
        )

        result = await self._make_request(form)
        _cache[cache_key] = result
        return result


    async def render(self, bypass_cache: bool = False) -> bytes:
        values = self.placeholder_values()
        payload = json.dumps(values.as_dict(), separators=(",", ":"), sort_keys=True)

        cache_key = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        if bypass_cache:
            form = FormData()
            form.add_field(
                "placeholder_values",
                payload.encode("utf-8"),
                filename="blob",
                content_type="application/json",
            )
            return await self._make_request(form)

        return await self._make_request_cached(cache_key, payload)


    async def render_to_buffer(self, bypass_cache: bool = False) -> BytesIO:
        render = await self.render(bypass_cache)
        buf = BytesIO(render)
        buf.seek(0)
        return buf


    @abstractmethod
    def placeholder_values(self) -> PlaceholderValues:
        ...
