from dataclasses import dataclass
from enum import Enum
from typing import final
from .types import TSpan
from .colors import Color, ColorString


@final
class PrestigeColorMaps:
    c = ColorString

    prestige_map = {
        10000: c.RED,
        900: c.DARK_PURPLE,
        800: c.BLUE,
        700: c.LIGHT_PURPLE,
        600: c.DARK_RED,
        500: c.DARK_AQUA,
        400: c.DARK_GREEN,
        300: c.AQUA,
        200: c.GOLD,
        100: c.WHITE,
        0: c.GRAY,
    }

    prestige_map_2 = {
        1100: (c.GRAY, c.WHITE, c.WHITE, c.WHITE, c.WHITE, c.GRAY, c.GRAY),
        1000: (c.RED, c.GOLD, c.YELLOW, c.GREEN, c.AQUA, c.LIGHT_PURPLE, c.DARK_PURPLE),
    }


class PrestigeColorEnum(Enum):
    SINGLE = 0
    MULTI = 1


PrestigeColorSingle = ColorString
PrestigeColorMulti = tuple[
    ColorString,
    ColorString,
    ColorString,
    ColorString,
    ColorString,
    ColorString,
    ColorString,
]


@dataclass
class PrestigeColorType:
    type: PrestigeColorEnum
    color: PrestigeColorSingle | PrestigeColorMulti


class PrestigeColors:
    def __init__(self, prestige: int) -> None:
        self._prestige = prestige
        self.__prestige_colors = None

    @property
    def prestige_colors(self) -> PrestigeColorType:
        if self.__prestige_colors is None:
            c = PrestigeColorMaps

            if 1000 <= self._prestige < 10000:
                thresholds = sorted(c.prestige_map_2.keys(), reverse=True)
                color = next(
                    (c.prestige_map_2[t] for t in thresholds if self._prestige >= t),
                    c.prestige_map_2[1000],
                )
                self.__prestige_colors = PrestigeColorType(
                    PrestigeColorEnum.MULTI,
                    tuple(col.value for col in color),
                )
                return self.__prestige_colors

            color = next(
                (c.prestige_map[t] for t in sorted(c.prestige_map.keys(), reverse=True) if self._prestige >= t),
                c.prestige_map[10000],
            )

            self.__prestige_colors = PrestigeColorType(
                PrestigeColorEnum.SINGLE,
                color.value,
            )

        return self.__prestige_colors

    @staticmethod
    def _single_prestige_color_gradient(color: Color):
        r, g, b = color.rgb
        rgbs = [
            (int(r * 0.56), int(g * 0.56), int(b * 0.56)),
            (int(r * 0.62), int(g * 0.62), int(b * 0.62)),
            (int(r * 0.68), int(g * 0.68), int(b * 0.68)),
            (int(r * 0.74), int(g * 0.74), int(b * 0.74)),
            (int(r * 0.82), int(g * 0.82), int(b * 0.82)),
            (int(r * 0.90), int(g * 0.90), int(b * 0.90)),
            (r, g, b),
        ]
        return tuple(Color(rgb) for rgb in rgbs)

    @property
    def seven_step_gradient(self):
        colors = self.prestige_colors.color
        if isinstance(colors, tuple):
            return colors
        return self._single_prestige_color_gradient(colors)


class Prestige:
    bedwars_star_symbol_map = {
        1100: "✪",
        0: "✫",
    }

    def __init__(self, level: int) -> None:
        self._level = level
        self.colors = PrestigeColors(self.prestige)

    @property
    def prestige(self) -> int:
        return self._level // 100 * 100

    @property
    def star_symbol(self) -> str:
        for key, value in self.bedwars_star_symbol_map.items():
            if self._level >= key:
                return value
        return "✫"

    def char_to_color_map(self) -> list[tuple[str, Color]]:
        text = f"[{self._level}{self.star_symbol}]"
        colors = self.colors.prestige_colors.color

        if isinstance(colors, tuple):
            return [(char, colors[i % len(colors)]) for i, char in enumerate(text)]

        return [(char, colors) for char in text]


ROLE_PREFIXES = {
    "Owner": [(ColorString.RED, "[Owner] ")],
    "Admin": [(ColorString.RED, "[Admin] ")],
    "Manager": [(ColorString.DARK_RED, "[Manager] ")],
    "Dev": [(ColorString.GREEN, "[Dev] ")],
    "HeadBuilder": [(ColorString.DARK_PURPLE, "[HeadBuilder] ")],
    "Builder": [(ColorString.LIGHT_PURPLE, "[Builder] ")],
    "SrMod": [(ColorString.YELLOW, "[SrMod] ")],
    "Mod": [(ColorString.YELLOW, "[Mod] ")],
    "Trainee": [(ColorString.GREEN, "[Trainee] ")],
    "Youtube": [
        (ColorString.RED, "["),
        (ColorString.WHITE, "Youtube"),
        (ColorString.RED, "] "),
    ],
    "Master": [(ColorString.GOLD, "[Master] ")],
    "Expert": [(ColorString.BLUE, "[Expert] ")],
    "Adept": [(ColorString.DARK_GREEN, "[Adept] ")],
    "Legend": [
        (ColorString.GOLD, "[Leg"),
        (ColorString.YELLOW, "en"),
        (ColorString.WHITE, "d"),
        (ColorString.GOLD, "] "),
    ],
}


ROLE_NAME_COLOR: dict[str, ColorString] = {
    "Owner": ColorString.RED,
    "Admin": ColorString.RED,
    "Manager": ColorString.DARK_RED,
    "Dev": ColorString.GREEN,
    "HeadBuilder": ColorString.DARK_PURPLE,
    "Builder": ColorString.LIGHT_PURPLE,
    "SrMod": ColorString.YELLOW,
    "Mod": ColorString.YELLOW,
    "Trainee": ColorString.GREEN,
    "Youtube": ColorString.RED,
    "Master": ColorString.GOLD,
    "Expert": ColorString.BLUE,
    "Adept": ColorString.DARK_GREEN,
    "Legend": ColorString.GOLD,
}


def format_legend_name(name: str) -> list[tuple[ColorString, str]]:
    if len(name) >= 3:
        return [
            (ColorString.GOLD, name[:-3]),
            (ColorString.YELLOW, name[-3:-1]),
            (ColorString.WHITE, name[-1]),
        ]
    if len(name) == 2:
        return [(ColorString.GOLD, name)]
    return [(ColorString.GOLD, name)]


def format_normal_name(name: str, role: str) -> list[tuple[ColorString, str]]:
    color = ROLE_NAME_COLOR.get(role, ColorString.GRAY)
    return [(color, name)]


def get_displayname(name: str, role: str) -> list[TSpan]:
    spans: list[TSpan] = []

    prefix_parts = ROLE_PREFIXES.get(role, [(ColorString.GRAY, "")])
    for color, text in prefix_parts:
        spans.extend(TSpan(char, color.value.hex) for char in text)

    name_parts = (
        format_legend_name(name) if role == "Legend" else format_normal_name(name, role)
    )

    for color, text in name_parts:
        spans.extend(TSpan(char, color.value.hex) for char in text)

    return spans