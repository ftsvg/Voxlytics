from typing import Protocol, Literal, Mapping


class PlayerProtocol(Protocol):
    game_stats: dict[str, dict[str, dict[str, int]]]


StatDict = dict[str, int]
StatsContainer = Mapping[str, StatDict]


def resolve_stats(
    player: PlayerProtocol,
    joins: tuple[str | None, str | None],
    view: Literal["single", "double", "combined"],
) -> StatDict:
    stats: StatsContainer = player.game_stats.get("stats", {})

    single, double = joins

    if view == "single" and single:
        return dict(stats.get(single, {}))

    if view == "double" and double:
        return dict(stats.get(double, {}))

    if view == "combined":
        s: StatDict = stats.get(single or "", {})
        d: StatDict = stats.get(double or "", {})

        return {
            k: s.get(k, 0) + d.get(k, 0)
            for k in (s.keys() | d.keys())
        }

    return {}