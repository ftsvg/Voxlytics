from enum import Enum


class VoxylApiEndpoint(Enum):
    PLAYER_INFO = "player/info/{uuid}"
    PLAYER_OVERALL = "player/stats/overall/{uuid}"
    PLAYER_STATS = "player/stats/game/{uuid}"
    PLAYER_GUILD = "player/guild/{uuid}"

    GUILD_INFO = "guild/info/{tag_or_id}"
    GUILD_MEMBERS = "guild/members/{tag_or_id}"
    GUILD_TOP = "guild/top"

    LEADERBOARD_NORMAL = "leaderboard/normal"
    LEADERBOARD_GAME = "leaderboard/game/{ref}"

    DISCORD_FROM_PLAYER = "integration/discord_from_player/{uuid}"
    PLAYER_FROM_DISCORD = "integration/player_from_discord/{discord_id}"