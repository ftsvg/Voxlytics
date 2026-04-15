from dataclasses import dataclass


@dataclass(frozen=True)
class ModeSchema:
    route: str
    stats: list[str]
    joins: tuple[str | None, str | None]
    types: dict[str, str]
    title: str


STAT_PRESETS: dict[int, list[str]] = {
    1: ["wins"],
    2: ["wins", "kills"],
    4: ["wins", "kills", "beds", "finals"],
    5: ["wins", "weighted", "kills", "finals", "beds"],
}


MODE_SCHEMAS: dict[str, ModeSchema] = {
    "Overall": ModeSchema(
        route="/stats-overall",
        stats=STAT_PRESETS[5],
        joins=("overall", None),
        types={"combined": "Overall"},
        title="Overall",
    ),
    "Bed Bridge Fight": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("bridgesSingle", "bridgesDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Bed Bridge Fight",
    ),
    "Void Fight": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("voidSingle", "voidDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Void Fight",
    ),
    "Ground Fight": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("groundSingle", "groundDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Ground Fight",
    ),
    "Bedwars Normal": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("bedwarsNormalSingle", "bedwarsNormalDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Bedwars Normal",
    ),
    "Ladder Fight": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("ladderFightSingle", "ladderFightDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Ladder Fight",
    ),
    "Miniwars": ModeSchema(
        route="/stats-4",
        stats=STAT_PRESETS[4],
        joins=("miniwarsSolo", "miniwarsDouble"),
        types={"single": "Solo", "double": "Doubles", "combined": "Overall"},
        title="Miniwars",
    ),
    "Block Sumo": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("sumo", None),
        types={"combined": "Overall"},
        title="Block Sumo",
    ),
    "Beta Block Sumo": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("betaSumo", None),
        types={"combined": "Overall"},
        title="Beta Block Sumo",
    ),
    "Sumo Duels": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("sumoDuelsSolo", "sumoDuelsDouble"),
        types={"single": "Solo", "double": "Doubles", "combined": "Overall"},
        title="Sumo Duels",
    ),
    "Stick Fight": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("stickFightSingle", "stickFightDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Stick Fight",
    ),
    "Pearl Fight": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("pearlFightSingle", "pearlFightDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Pearl Fight",
    ),
    "Bed Rush": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("bedRushSingle", "bedRushDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Bed Rush",
    ),
    "Bow Fight": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("bowFightSingle", "bowFightDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Bow Fight",
    ),
    "Flat Fight": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("flatFightSingle", "flatFightDouble"),
        types={"single": "1v1", "double": "2v2", "combined": "Overall"},
        title="Flat Fight",
    ),
    "Resource Collect": ModeSchema(
        route="/stats-2",
        stats=STAT_PRESETS[2],
        joins=("resourceSingle", "resourceDouble"),
        types={"single": "Solo", "double": "Doubles", "combined": "Overall"},
        title="Resource Collect",
    ),
    "Obstacles": ModeSchema(
        route="/stats-1",
        stats=STAT_PRESETS[1],
        joins=("obstacleSingle", None),
        types={"combined": "Overall"},
        title="Obstacles",
    ),
    "Party Games": ModeSchema(
        route="/stats-1",
        stats=STAT_PRESETS[1],
        joins=("partyGames", None),
        types={"combined": "Overall"},
        title="Party Games",
    ),
}