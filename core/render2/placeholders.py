import json
import typing
from collections.abc import Mapping
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, UTC

import aiohttp

from .types import TSpan
from .utils import Prestige, PrestigeColors, get_displayname
from core import get_xp_for_level, ordinal


@dataclass
class PlaceholderValues:
    images: dict[str, str]
    shapes: dict[str, str]
    text: dict[str, str | TSpan | list[TSpan]]

    @staticmethod
    def new(
        text: Mapping[str, str | TSpan | list[TSpan]] | None = None,
        images: dict[str, str] | None = None,
        shapes: dict[str, str] | None = None,
    ) -> "PlaceholderValues":
        return PlaceholderValues(
            text=dict(text or {}),
            shapes=shapes or {},
            images=images or {},
        )

    def as_dict(self) -> dict[str, typing.Any]:
        text = {}

        for k, v in self.text.items():
            if isinstance(v, str):
                text[k] = v
            elif isinstance(v, list):
                text[k] = [t.as_dict() for t in v]
            elif isinstance(v, TSpan):
                text[k] = v.as_dict()

        return {
            "images": self.images,
            "shapes": self.shapes,
            "text": text,
        }


    def add_progress_bar(self, level: int, xp: int) -> None:
        xp_needed = get_xp_for_level(level)
        progress_percent = 0 if xp_needed == 0 else max(min((xp / xp_needed) * 100, 100), 0)

        fill_width = (progress_percent / 100) * 470

        self.shapes["progress_bar#width"] = f"{fill_width}px"

        colors = PrestigeColors(level).seven_step_gradient

        for i, color in enumerate(colors):
            self.shapes[f"progress_bar#gradientStop.{i}"] = color.hex



    def add_skin_model(
        self, skin_model_bytes: bytes, placeholder_key: str = "skin"
    ) -> None:
        skin_base64 = b64encode(skin_model_bytes).decode("utf-8")
        self.images[f"{placeholder_key}#href"] = f"data:image/png;base64,{skin_base64}"


    def add_footer(self) -> None:
        now = datetime.now(UTC)
        self.text["footer#text"] = [
            TSpan(value="voxlytics.net • ", fill="#FFFFFF"),
            TSpan(
                value=now.strftime(f"%A %d{ordinal(now.day)} %B, %Y"), fill="#AAAAAA"
            ),
        ]


    def add_current_level(
        self, current_level: int, placeholder_key: str = "level"
    ) -> None:
        prestige = Prestige(current_level)
        self.text[f"{placeholder_key}#text"] = [
            TSpan(value=char, fill=color.hex)
            for char, color in prestige.char_to_color_map()
        ]


    def add_next_level(
        self, next_level: int, placeholder_key: str = "level_next"
    ) -> None:
        prestige = Prestige(next_level)
        self.text[f"{placeholder_key}#text"] = [
            TSpan(value=char, fill=color.hex)
            for char, color in prestige.char_to_color_map()
        ]


    def add_current_and_next_level(self, current_level: int) -> None:
        self.add_current_level(current_level)
        self.add_next_level(current_level + 1)


    def add_progress_text(self, level: int, xp: int) -> None:
        xp_needed = get_xp_for_level(level)

        self.text["xp_progress#text"] = [
            TSpan(value=f"{xp:,} ", fill="#55FFFF"),
            TSpan(value="/ ", fill="#555555"),
            TSpan(value=f"{xp_needed:,} ", fill="#55FF55"),
            TSpan(value="xp", fill="#AAAAAA"),
        ]


    def add_displayname(
        self, name: str, role: str, placeholder_key: str = "displayname"
    ) -> None:
        spans = get_displayname(name, role)
        self.text[f"{placeholder_key}#text"] = [
            TSpan(value=span.value, fill=span.fill) for span in spans
        ]

    def ad_displayname_star(
        self,
        name: str,
        role: str,
        level: int,
        placeholder_key: str = "displayname",
    ) -> None:
        prestige = Prestige(level)

        spans: list[TSpan] = [
            TSpan(value=char, fill=color.hex)
            for char, color in prestige.char_to_color_map()
        ]

        spans.append(TSpan(value=" "))
        spans.extend(get_displayname(name, role))

        self.text[f"{placeholder_key}#text"] = spans


    def build_form_data(self) -> aiohttp.FormData:
        data = aiohttp.FormData()
        payload = json.dumps(self.as_dict(), separators=(",", ":"))
        data.add_field(
            "placeholder_values",
            payload.encode("utf-8"),
            filename="blob",
            content_type="application/json",
        )
        return data

