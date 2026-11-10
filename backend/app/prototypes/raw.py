from typing import NamedTuple


class RawScreen(NamedTuple):
    name: str
    png: bytes


class RawStart(NamedTuple):
    name: str
    screens: tuple[RawScreen, ...]


class RawPrototype(NamedTuple):
    name: str
    starts: tuple[RawStart, ...]
