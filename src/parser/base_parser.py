from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d+:\d+:\d+\.\d+)\s+"
    r"(?P<pid>\d+)\s+"
    r"(?P<thread>0x[0-9a-fA-F]+)\s+"
    r"(?P<level>\w+)\s+"
    r"(?P<domain>\S+)\s+"
    r"(?P<payload>.+)$"
)

PAD_TAG_RE = re.compile(r"<(?P<element>[a-zA-Z0-9_]+):(?P<pad>[a-zA-Z0-9_]+)>")
ELEMENT_TAG_RE = re.compile(r"<(?P<element>[a-zA-Z0-9_]+)>")
CALLSITE_RE = re.compile(r":(?P<func>[a-zA-Z0-9_]+):<(?P<object>[^>]+)>")


@dataclass(frozen=True)
class LogLine:
    raw: str
    ts_str: str
    ts: float
    level: str
    domain: str
    payload: str


class GstLogLineParser:
    def parse(self, raw: str) -> Optional[LogLine]:
        clean = ANSI_ESCAPE_RE.sub("", raw).strip()
        m = LOG_LINE_RE.match(clean)
        if not m:
            return None
        ts_str = m.group("ts")
        return LogLine(
            raw=raw,
            ts_str=ts_str,
            ts=self._parse_timestamp_seconds(ts_str),
            level=m.group("level"),
            domain=m.group("domain"),
            payload=m.group("payload"),
        )

    def extract_first_pad(self, payload: str) -> Optional[tuple[str, str]]:
        m = PAD_TAG_RE.search(payload)
        if not m:
            return None
        return m.group("element"), m.group("pad")

    def extract_first_element(self, payload: str) -> Optional[str]:
        m = ELEMENT_TAG_RE.search(payload)
        if not m:
            return None
        return m.group("element")

    def extract_callsite(self, payload: str) -> Optional[str]:
        m = CALLSITE_RE.search(payload)
        if not m:
            return None
        return f"{m.group('func')}:<{m.group('object')}>"

    def _parse_timestamp_seconds(self, ts: str) -> float:
        parts = ts.split(":")
        if len(parts) != 3:
            return 0.0
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600.0 + m * 60.0 + s


class BaseParser:
    def handle(self, line: LogLine, registry) -> None:
        raise NotImplementedError
