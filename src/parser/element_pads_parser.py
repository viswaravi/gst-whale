from __future__ import annotations

import re

from model.events import PadLinkAttempt, PadLinkFailure, PadLinkSuccess
from parser.base_parser import BaseParser, LogLine
from registry.gst_registry import GstRegistry


LINK_ATTEMPT_RE = re.compile(
    r"trying to link element\s+"
    r"(?P<src_elem>\w+):(?P<src_pad>\w+|\(any\))\s+"
    r"to element\s+"
    r"(?P<sink_elem>\w+):(?P<sink_pad>\w+|\(any\))"
)

LINK_SUCCESS_RE = re.compile(
    r"linked\s+"
    r"(?P<src_elem>\w+):(?P<src_pad>\w+)\s+and\s+"
    r"(?P<sink_elem>\w+):(?P<sink_pad>\w+),\s+successful"
)

LINK_FAIL_RE = re.compile(r"link.*(failed|fail)", re.IGNORECASE)


class ElementPadsParser(BaseParser):
    def handle(self, line: LogLine, registry: GstRegistry) -> None:
        m = LINK_ATTEMPT_RE.search(line.payload)
        if m:
            src_pad_name = m.group("src_pad")
            sink_pad_name = m.group("sink_pad")
            if src_pad_name == "(any)":
                src_pad_name = "(any)"
            if sink_pad_name == "(any)":
                sink_pad_name = "(any)"

            src = registry.get_or_create_pad(m.group("src_elem"), src_pad_name)
            sink = registry.get_or_create_pad(m.group("sink_elem"), sink_pad_name)
            link_key = registry.set_link_context(src, sink)

            registry.add_event(
                PadLinkAttempt(ts=line.ts, link_key=link_key, order=registry.next_order(), src=src, sink=sink)
            )
            return

        m = LINK_SUCCESS_RE.search(line.payload)
        if m:
            src = registry.get_or_create_pad(m.group("src_elem"), m.group("src_pad"))
            sink = registry.get_or_create_pad(m.group("sink_elem"), m.group("sink_pad"))
            link_key = registry.set_link_context(src, sink)
            registry.links.add((src.key, sink.key))
            registry.add_event(
                PadLinkSuccess(ts=line.ts, link_key=link_key, order=registry.next_order(), src=src, sink=sink)
            )
            registry.mark_link_success(link_key)
            return

        if LINK_FAIL_RE.search(line.payload):
            return
