from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


def get_xp_for_level(level: int) -> int:
    cycle = {
        0: 1000,
        1: 2000,
        2: 3000,
        3: 4000,
        4: 5000,
    }

    cycle_level = level % 100
    if cycle_level in cycle:
        return cycle[cycle_level]

    block = level // 100

    base_xp = 5000
    increment = 500

    if block <= 20:
        return base_xp + (block * increment)

    return base_xp + (20 * increment)


def get_total_xp(level: int, partial_xp: int = 0) -> int:
    total_xp = 0
    for lvl in range(1, level):
        total_xp += get_xp_for_level(lvl)

    total_xp += partial_xp
    
    return total_xp


def get_xp_and_stars(
    old_level: int, old_xp: int, new_level: int, new_xp: int
) -> tuple[int, float]:

    old = get_total_xp(old_level, old_xp)
    new = get_total_xp(new_level, new_xp)

    xp_gained = new - old
    stars_gained = round(xp_gained / 5000, 2)

    return xp_gained, stars_gained


def get_stars_gained(
    old_level: int,
    old_xp: int,
    new_level: int,
    new_xp: int
) -> float:
    old_total_xp = get_total_xp(old_level, old_xp)
    new_total_xp = get_total_xp(new_level, new_xp)

    xp_gained = new_total_xp - old_total_xp
    stars_gained = round(xp_gained / 5000, 2)

    return stars_gained


def fmt(value, color="&f") -> str:
    return f"{color}{value:,}"


def ordinal(n: int) -> str:
    if 4 <= n % 100 <= 20:
        return "th"
    
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
