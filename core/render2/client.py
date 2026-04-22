import os
import json
import hashlib
from typing import Hashable, Sequence
from abc import ABC, abstractmethod
from io import BytesIO

from dotenv import load_dotenv

import cachetools.keys
from aiohttp import ClientSession, ClientTimeout
from cachetools import TTLCache
from cachetools_async import cached

from core import logger
from .placeholders import PlaceholderValues
from .background import load_background_for_user

load_dotenv()


def exclude_self_key(*args: Sequence[Hashable], **kwargs: frozenset[Hashable]):
    return cachetools.keys.hashkey(*args[1:], **kwargs)


class RenderingClient(ABC):
    def __init__(self, route: str) -> None:
        self._route = route.removeprefix("/")

    @staticmethod
    def bg(
        discord_id: int,
    ) -> bytes | None:
        return load_background_for_user(discord_id)


    async def _make_request(
        self, placeholder_values: PlaceholderValues, background_image: bytes | None
    ) -> bytes:
        formdata = placeholder_values.build_form_data(background_image)

        async with ClientSession(timeout=ClientTimeout(total=10)) as session:
            res = await session.post(
                f"{os.getenv('RENDERER_HOSTNAME')}/{self._route}", data=formdata
            )
            res.raise_for_status()

            render_bytes = await res.content.read()

        return render_bytes


    @cached(cache=TTLCache(ttl=600, maxsize=20), key=exclude_self_key)
    async def _make_request_with_cache(
        self, placeholder_values: PlaceholderValues, background_image: bytes | None
    ) -> bytes:
        logger.debug("LRU renderer cache miss.")
        return await self._make_request(placeholder_values, background_image)


    async def render(
        self,
        background_image: bytes | None = None,
        bypass_cache: bool = False
    ) -> bytes:
        if bypass_cache:
            return await self._make_request(self.placeholder_values(), background_image)

        return await self._make_request_with_cache(
            self.placeholder_values(), background_image
        )


    async def render_to_buffer(
        self, background_image: bytes | None = None, bypass_cache: bool = False
    ) -> BytesIO:
        render = await self.render(background_image, bypass_cache)

        img_bytes = BytesIO(render)
        _ = img_bytes.seek(0)

        return img_bytes


    @abstractmethod
    def placeholder_values(self) -> PlaceholderValues:
        ...