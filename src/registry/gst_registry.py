from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from gst_trace_cli.model.element import GstElement
from gst_trace_cli.model.events import (
    CapsCompatible,
    CapsFiltered,
    CapsQueryStart,
    CapsResolved,
    CapsTemplateUsed,
    GstEvent,
    LinkKey,
    PadLinkAttempt,
    PadLinkFailure,
    PadLinkSuccess,
)
from gst_trace_cli.model.pad import GstPad


@dataclass
class ActiveCapsQuery:
    target: GstPad
    start_ts: float
    start_emitted: bool = False
    peer_missing: bool = False
    template_caps: Optional[str] = None
    template_emitted: bool = False
    filtered_caps: Optional[str] = None
    filtered_emitted: bool = False
    final_caps: Optional[str] = None
    resolved_emitted: bool = False
    compatible_emitted: bool = False


@dataclass
class GstRegistry:
    elements: dict[str, GstElement] = field(default_factory=dict)
    pads: dict[str, GstPad] = field(default_factory=dict)
    links: set[tuple[str, str]] = field(default_factory=set)
    events: list[GstEvent] = field(default_factory=list)

    active_caps_queries: dict[str, list[ActiveCapsQuery]] = field(default_factory=dict)
    last_link_key_for_pad: dict[str, LinkKey] = field(default_factory=dict)

    last_link_key_for_element: dict[str, LinkKey] = field(default_factory=dict)

    link_attempts: dict[LinkKey, GstPad] = field(default_factory=dict)
    link_success: set[LinkKey] = field(default_factory=set)
    link_failure: set[LinkKey] = field(default_factory=set)
    caps_resolved: set[LinkKey] = field(default_factory=set)

    last_seen_pad_for_element: dict[str, GstPad] = field(default_factory=dict)

    last_caps_resolved_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_caps_filtered_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_caps_template_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_caps_peer_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_caps_intersection_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_reconfigure_ts_by_context: dict[tuple[LinkKey, str], float] = field(default_factory=dict)
    last_query_request_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)
    last_peer_query_request_by_context: dict[tuple[LinkKey, str], str] = field(default_factory=dict)

    _event_order: int = 0

    def next_order(self) -> int:
        self._event_order += 1
        return self._event_order

    def get_or_create_element(self, name: str) -> GstElement:
        el = self.elements.get(name)
        if el is None:
            el = GstElement(name=name)
            self.elements[name] = el
        return el

    def get_or_create_pad(self, element_name: str, pad_name: str) -> GstPad:
        self.get_or_create_element(element_name)
        key = f"{element_name}:{pad_name}"
        pad = self.pads.get(key)
        if pad is None:
            pad = GstPad(element_name=element_name, pad_name=pad_name)
            self.pads[key] = pad
        self.last_seen_pad_for_element[element_name] = pad
        return pad

    def set_link_context(self, src: GstPad, sink: GstPad) -> LinkKey:
        link_key: LinkKey = (src.element_name, sink.element_name)
        self.last_link_key_for_pad[src.key] = link_key
        self.last_link_key_for_pad[sink.key] = link_key
        self.last_link_key_for_element[src.element_name] = link_key
        self.last_link_key_for_element[sink.element_name] = link_key
        self.link_attempts[link_key] = src
        self._rebind_events_for_context(
            pad_keys={src.key, sink.key},
            element_names={src.element_name, sink.element_name},
            link_key=link_key,
        )
        return link_key

    def _rebind_events_for_context(
        self,
        pad_keys: set[str],
        element_names: set[str],
        link_key: LinkKey,
    ) -> None:
        for ev in self.events:
            if getattr(ev, "link_key", None) is None:
                continue
            if ev.link_key[1] != "UNKNOWN":
                continue
            target = getattr(ev, "target", None)
            if target is None:
                continue
            target_key = getattr(target, "key", None)
            target_element = getattr(target, "element_name", None)
            if target_key not in pad_keys and target_element not in element_names:
                continue
            ev.link_key = link_key

    def link_key_for_pad(self, pad: GstPad) -> LinkKey:
        lk = self.last_link_key_for_pad.get(pad.key)
        if lk is not None:
            return lk
        lk = self.last_link_key_for_element.get(pad.element_name)
        if lk is not None:
            return lk
        return (pad.element_name, "UNKNOWN")

    def add_event(self, ev: GstEvent) -> None:
        self.events.append(ev)

    def ensure_caps_query(self, ts: float, target: GstPad) -> ActiveCapsQuery:
        q = self.get_active_caps_query(target)
        if q is not None:
            return q
        q = ActiveCapsQuery(target=target, start_ts=ts)
        self.active_caps_queries.setdefault(target.key, []).append(q)
        return q

    def start_caps_query(self, ts: float, target: GstPad, reason: Optional[str]) -> ActiveCapsQuery:
        q = ActiveCapsQuery(target=target, start_ts=ts)
        self.active_caps_queries.setdefault(target.key, []).append(q)
        self.add_event(CapsQueryStart(ts=ts, link_key=self.link_key_for_pad(target), order=self.next_order(), target=target, reason=reason))
        q.start_emitted = True
        return q

    def get_active_caps_query(self, target: GstPad) -> Optional[ActiveCapsQuery]:
        stack = self.active_caps_queries.get(target.key)
        if not stack:
            return None
        return stack[-1]

    def get_most_recent_active_caps_query_for_element(self, element_name: str) -> Optional[ActiveCapsQuery]:
        newest: Optional[ActiveCapsQuery] = None
        for stack in self.active_caps_queries.values():
            if not stack:
                continue
            q = stack[-1]
            if q.target.element_name != element_name:
                continue
            if newest is None or q.start_ts > newest.start_ts:
                newest = q
        return newest

    def get_most_recent_active_caps_query(self) -> Optional[ActiveCapsQuery]:
        newest: Optional[ActiveCapsQuery] = None
        for stack in self.active_caps_queries.values():
            if not stack:
                continue
            q = stack[-1]
            if newest is None or q.start_ts > newest.start_ts:
                newest = q
        return newest

    def close_active_caps_query(self, target: GstPad) -> Optional[ActiveCapsQuery]:
        stack = self.active_caps_queries.get(target.key)
        if not stack:
            return None
        q = stack.pop()
        if not stack:
            self.active_caps_queries.pop(target.key, None)
        return q

    def mark_link_success(self, link_key: LinkKey) -> None:
        self.link_success.add(link_key)

    def mark_link_failure(self, link_key: LinkKey) -> None:
        self.link_failure.add(link_key)

    def mark_caps_resolved(self, link_key: LinkKey) -> None:
        self.caps_resolved.add(link_key)

    def finalize(self) -> None:
        last_ts_for_link: dict[LinkKey, float] = {}
        last_src_sink_for_link: dict[LinkKey, tuple[GstPad, GstPad]] = {}

        for ev in self.events:
            last_ts_for_link[ev.link_key] = ev.ts
            if isinstance(ev, PadLinkAttempt):
                last_src_sink_for_link[ev.link_key] = (ev.src, ev.sink)

        for link_key in sorted(self.caps_resolved):
            if link_key in self.link_success or link_key in self.link_failure:
                continue
            ts = last_ts_for_link.get(link_key)
            pads = last_src_sink_for_link.get(link_key)
            if ts is None or pads is None:
                continue
            src, sink = pads
            self.add_event(PadLinkSuccess(ts=ts, link_key=link_key, order=self.next_order(), src=src, sink=sink, inferred=True))
            self.link_success.add(link_key)
