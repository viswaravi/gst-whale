from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GstPad:
    element_name: str
    pad_name: str

    @property
    def key(self) -> str:
        return f"{self.element_name}:{self.pad_name}"
