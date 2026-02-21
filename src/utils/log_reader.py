from __future__ import annotations

from typing import Iterable


class LogReader:
    def __init__(self, path: str):
        self.path = path

    def lines(self) -> Iterable[str]:
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line.rstrip("\n")
