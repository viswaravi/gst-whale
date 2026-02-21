from __future__ import annotations

import re

from model.events import (
    CapsCompatible,
    CapsFiltered,
    CapsIntersection,
    CapsOurTemplate,
    CapsPeerCaps,
    CapsPeerFilter,
    CapsPeerQueryRequest,
    CapsQueryRequest,
    CapsQueryResult,
    CapsResolved,
    CapsReturning,
    CapsSinkCapsCheck,
    CapsTemplateUsed,
    CapsTransformInput,
    CapsTransformTo,
    CapsTransformed,
    ReconfigureTriggered,
)
from parser.base_parser import BaseParser, LogLine
from parser.base_parser import GstLogLineParser
from registry.gst_registry import GstRegistry


PEER_MISSING_RE = re.compile(r"pad has no peer")
QUERY_CAPS_REQUEST_RE = re.compile(r"get pad caps with filter\s+(?P<filter>.+)")
PEER_QUERY_CAPS_REQUEST_RE = re.compile(r"get pad peer caps with filter\s+(?P<filter>.+)")
TEMPLATE_RE = re.compile(r"other template\s+(?P<caps>.+)")
OUR_TEMPLATE_RE = re.compile(r"our template\s+(?P<caps>.+)")
CAPS_FILTER_RE = re.compile(r"caps filter:\s*(?P<caps>.+)")
QUERY_RETURNED_RE = re.compile(r"query returned\s+(?P<caps>.+)")
PEER_FILTER_CAPS_RE = re.compile(r"peer filter caps\s+(?P<caps>.+)")
PEER_CAPS_WITH_FILTER_RE = re.compile(r"peer caps\s+with filter\s+(?P<caps>.+)")
PEER_CAPS_RE = re.compile(r"peer caps\s+(?P<caps>.+)")
INTERSECTED_RE = re.compile(r"intersected\s+(?P<caps>.+)")
INTERSECT_RE = re.compile(r"intersect:\s*(?P<caps>.+)")
SINK_CAPS_RE = re.compile(r"sink caps\s+(?P<caps>.+)")
TRANSFORM_INPUT_RE = re.compile(r"input:\s*(?P<caps>.+)")
TRANSFORM_TO_RE = re.compile(r"\bto:\s*(?P<caps>.+)")
TRANSFORMED_RE = re.compile(r"transformed\s+(?P<caps>.+)")
RETURNING_RE = re.compile(r"returning\s+(?P<caps>.+)")
QUERY_RESULT_RE = re.compile(r"sent query\s+0x[0-9a-fA-F]+\s+\(caps\),\s+result\s+(?P<result>\d+)")
CAPS_COMPATIBLE_RE = re.compile(r"caps are compatible")
NON_CAPS_RESULT_RE = re.compile(r"^\s*(?:0|1)\s*$")
RECONFIGURE_RE = re.compile(r"creating reconfigure event")


class CapsParser(BaseParser):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._line_parser = GstLogLineParser()

    def handle(self, line: LogLine, registry: GstRegistry) -> None:
        via = self._line_parser.extract_callsite(line.payload)
        if RECONFIGURE_RE.search(line.payload):
            target = self._resolve_target_pad(line, registry)
            if target is None:
                q_any = registry.get_most_recent_active_caps_query()
                if q_any is None:
                    return
                target = q_any.target
            link_key = registry.link_key_for_pad(target)
            ctx_key = (link_key, target.key)
            last_ts = registry.last_reconfigure_ts_by_context.get(ctx_key)
            if last_ts is not None and abs(last_ts - line.ts) < 1e-9:
                return
            registry.last_reconfigure_ts_by_context[ctx_key] = line.ts
            ev = ReconfigureTriggered(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target)
            ev.via = via
            registry.add_event(ev)
            return

        target = self._resolve_target_pad(line, registry)
        if target is None:
            if CAPS_COMPATIBLE_RE.search(line.payload):
                q_any = registry.get_most_recent_active_caps_query()
                if q_any is None:
                    return
                target = q_any.target
                link_key = registry.link_key_for_pad(target)
                if not q_any.compatible_emitted:
                    ev = CapsCompatible(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target)
                    ev.via = via
                    registry.add_event(ev)
                    q_any.compatible_emitted = True
            return
        link_key = registry.link_key_for_pad(target)

        m = QUERY_CAPS_REQUEST_RE.search(line.payload)
        if m:
            f = m.group("filter").strip()
            ctx_key = (link_key, target.key)
            if registry.last_query_request_by_context.get(ctx_key) == f:
                return
            registry.last_query_request_by_context[ctx_key] = f
            ev = CapsQueryRequest(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, filter_caps=f)
            ev.via = via
            registry.add_event(ev)
            return

        m = PEER_QUERY_CAPS_REQUEST_RE.search(line.payload)
        if m:
            f = m.group("filter").strip()
            ctx_key = (link_key, target.key)
            if registry.last_peer_query_request_by_context.get(ctx_key) == f:
                return
            registry.last_peer_query_request_by_context[ctx_key] = f
            ev = CapsPeerQueryRequest(
                ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, filter_caps=f
            )
            ev.via = via
            registry.add_event(ev)
            return

        m = PEER_CAPS_WITH_FILTER_RE.search(line.payload)
        if m:
            return

        m = QUERY_RESULT_RE.search(line.payload)
        if m:
            result = int(m.group("result"))
            ev = CapsQueryResult(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, result=result)
            ev.via = via
            registry.add_event(ev)
            return

        m = PEER_FILTER_CAPS_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            if caps.lower() == "(null)":
                caps = "(NULL)"
            ctx_key = (link_key, target.key)
            if registry.last_caps_peer_by_context.get(ctx_key) == f"peer-filter:{caps}":
                return
            registry.last_caps_peer_by_context[ctx_key] = f"peer-filter:{caps}"
            ev = CapsPeerFilter(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        if PEER_MISSING_RE.search(line.payload):
            q = registry.get_active_caps_query(target)
            if q is None:
                q = registry.start_caps_query(ts=line.ts, target=target, reason="peer missing → template fallback")
            q.peer_missing = True
            return

        m = PEER_CAPS_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ctx_key = (link_key, target.key)
            if registry.last_caps_peer_by_context.get(ctx_key) == caps:
                return
            registry.last_caps_peer_by_context[ctx_key] = caps
            ev = CapsPeerCaps(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = TRANSFORM_INPUT_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ev = CapsTransformInput(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = TRANSFORM_TO_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ev = CapsTransformTo(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = TRANSFORMED_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ev = CapsTransformed(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = RETURNING_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ev = CapsReturning(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = TEMPLATE_RE.search(line.payload)
        if m:
            q = registry.ensure_caps_query(ts=line.ts, target=target)
            q.template_caps = m.group("caps").strip()
            if not q.template_emitted:
                ctx_key = (link_key, target.key)
                if registry.last_caps_template_by_context.get(ctx_key) == q.template_caps:
                    return
                registry.last_caps_template_by_context[ctx_key] = q.template_caps
                ev = CapsTemplateUsed(
                    ts=line.ts,
                    link_key=link_key,
                    order=registry.next_order(),
                    target=target,
                    caps=q.template_caps,
                )
                ev.via = via
                registry.add_event(ev)
                q.template_emitted = True
            return

        m = OUR_TEMPLATE_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ctx_key = (link_key, target.key)
            if registry.last_caps_template_by_context.get(ctx_key) == caps:
                return
            registry.last_caps_template_by_context[ctx_key] = caps
            ev = CapsOurTemplate(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = CAPS_FILTER_RE.search(line.payload)
        if m:
            q = registry.ensure_caps_query(ts=line.ts, target=target)
            q.filtered_caps = m.group("caps").strip()
            if not q.filtered_emitted:
                ctx_key = (link_key, target.key)
                if registry.last_caps_filtered_by_context.get(ctx_key) == q.filtered_caps:
                    return
                registry.last_caps_filtered_by_context[ctx_key] = q.filtered_caps
                ev = CapsFiltered(
                    ts=line.ts,
                    link_key=link_key,
                    order=registry.next_order(),
                    target=target,
                    caps=q.filtered_caps,
                )
                ev.via = via
                registry.add_event(ev)
                q.filtered_emitted = True
            return

        m = INTERSECT_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ctx_key = (link_key, target.key)
            if registry.last_caps_intersection_by_context.get(ctx_key) == caps:
                return
            registry.last_caps_intersection_by_context[ctx_key] = caps
            ev = CapsIntersection(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = INTERSECTED_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ctx_key = (link_key, target.key)
            if registry.last_caps_intersection_by_context.get(ctx_key) == caps:
                return
            registry.last_caps_intersection_by_context[ctx_key] = caps
            ev = CapsIntersection(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        m = QUERY_RETURNED_RE.search(line.payload)
        if m:
            q = registry.ensure_caps_query(ts=line.ts, target=target)
            q.final_caps = m.group("caps").strip()
            if NON_CAPS_RESULT_RE.match(q.final_caps):
                return
            if not q.resolved_emitted:
                ctx_key = (link_key, target.key)
                if registry.last_caps_resolved_by_context.get(ctx_key) == q.final_caps:
                    return
                registry.last_caps_resolved_by_context[ctx_key] = q.final_caps
                ev = CapsResolved(
                    ts=line.ts,
                    link_key=link_key,
                    order=registry.next_order(),
                    target=target,
                    caps=q.final_caps,
                )
                ev.via = via
                registry.add_event(ev)
                q.resolved_emitted = True
                registry.mark_caps_resolved(link_key)
                registry.close_active_caps_query(target)
            return

        m = SINK_CAPS_RE.search(line.payload)
        if m:
            caps = m.group("caps").strip()
            ev = CapsSinkCapsCheck(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target, caps=caps)
            ev.via = via
            registry.add_event(ev)
            return

        if CAPS_COMPATIBLE_RE.search(line.payload):
            q = registry.get_active_caps_query(target)
            if q is None:
                return
            if not q.compatible_emitted:
                ev = CapsCompatible(ts=line.ts, link_key=link_key, order=registry.next_order(), target=target)
                ev.via = via
                registry.add_event(ev)
                q.compatible_emitted = True
            return

    def _resolve_target_pad(self, line: LogLine, registry: GstRegistry):
        ep = self._line_parser.extract_first_pad(line.payload)
        if ep is not None:
            elem, pad = ep
            return registry.get_or_create_pad(elem, pad)

        elem_only = self._line_parser.extract_first_element(line.payload)
        if elem_only is None:
            return None

        q = registry.get_most_recent_active_caps_query_for_element(elem_only)
        if q is not None:
            return q.target
        return None


 
