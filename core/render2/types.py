from dataclasses import dataclass
import typing


@dataclass(unsafe_hash=True)
class TSpan:
    value: str
    fill: str | None = None

    def as_dict(self) -> dict[str, typing.Any]:
        return self.__dict__