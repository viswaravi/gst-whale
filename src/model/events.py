from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from gst_trace_cli.model.pad import GstPad


LinkKey = tuple[str, str]


def _truncate(s: str, max_len: int = 160) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


@dataclass
class GstEvent:
    ts: float
    link_key: LinkKey
    order: int
    via: Optional[str] = field(default=None, init=False)

    def _lines_with_via(self, detail: list[str]) -> list[str]:
        if self.via:
            return [f"  Via: {self.via}", *detail]
        return detail

    def title(self) -> str:
        raise NotImplementedError

    def lines(self) -> list[str]:
        raise NotImplementedError


@dataclass
class PadLinkAttempt(GstEvent):
    src: GstPad
    sink: GstPad

    def title(self) -> str:
        return "LINK ATTEMPT"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {self.src.key} → {self.sink.key}"])


@dataclass
class PadLinkSuccess(GstEvent):
    src: GstPad
    sink: GstPad
    inferred: bool = False

    def title(self) -> str:
        return "LINK SUCCESS"

    def lines(self) -> list[str]:
        if self.inferred:
            return self._lines_with_via(["  inferred"])
        return self._lines_with_via([])


@dataclass
class PadLinkFailure(GstEvent):
    src: GstPad
    sink: GstPad
    reason: Optional[str] = None

    def title(self) -> str:
        return "LINK FAILURE"

    def lines(self) -> list[str]:
        if self.reason:
            return self._lines_with_via([f"  {self.reason}"])
        return self._lines_with_via([])


@dataclass
class CapsQueryStart(GstEvent):
    target: GstPad
    reason: Optional[str] = None

    def title(self) -> str:
        return "CAPS QUERY START"

    def lines(self) -> list[str]:
        out = [f"  Target pad: {self.target.key}"]
        if self.reason:
            out.append(f"  Reason: {self.reason}")
        return self._lines_with_via(out)


@dataclass
class CapsQueryRequest(GstEvent):
    target: GstPad
    filter_caps: str

    def title(self) -> str:
        return "QUERY CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  Filter: {_truncate(self.filter_caps)}"])


@dataclass
class CapsPeerQueryRequest(GstEvent):
    target: GstPad
    filter_caps: str

    def title(self) -> str:
        return "PEER QUERY CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  Filter: {_truncate(self.filter_caps)}"])


@dataclass
class CapsTemplateUsed(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "TEMPLATE CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsPeerFilter(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "PEER FILTER CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsTransformInput(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "TRANSFORM INPUT CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsTransformTo(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "TRANSFORM TO CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsTransformed(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "TRANSFORMED CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsReturning(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "RETURNING CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsFiltered(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "CAPS FILTER"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsResolved(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        if self.target.pad_name == "src":
            return "PRODUCER CAPS"
        if self.target.pad_name == "sink":
            return "ACCEPT CAPS"
        return "CAPS RESULT"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsCompatible(GstEvent):
    target: GstPad

    def title(self) -> str:
        return "CAPS COMPATIBLE"

    def lines(self) -> list[str]:
        return self._lines_with_via([])


@dataclass
class CapsPeerCaps(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "PEER CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsIntersection(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "INTERSECTION CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class ReconfigureTriggered(GstEvent):
    target: GstPad

    def title(self) -> str:
        return "RECONFIGURE"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  Target pad: {self.target.key}"])


@dataclass
class CapsQueryResult(GstEvent):
    target: GstPad
    result: int

    def title(self) -> str:
        return "CAPS QUERY RESULT"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  Result: {self.result}"])


@dataclass
class CapsOurTemplate(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "OUR TEMPLATE CAPS"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsSrcCapsCheck(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "SRC CAPS CHECK"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])


@dataclass
class CapsSinkCapsCheck(GstEvent):
    target: GstPad
    caps: str

    def title(self) -> str:
        return "SINK CAPS CHECK"

    def lines(self) -> list[str]:
        return self._lines_with_via([f"  {_truncate(self.caps)}"])
