from core.api import API, VoxylApiEndpoint


class LeaderboardInfo:
    @staticmethod
    async def fetch_leaderboard(
        _type: str,
        num: int = 100,
    ) -> dict | int:
        return await API.request(
            VoxylApiEndpoint.LEADERBOARD_NORMAL,
            type=_type,
            num=num,
        )