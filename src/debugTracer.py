from __future__ import annotations

import argparse

from gst_trace_cli.parser.base_parser import GstLogLineParser
from gst_trace_cli.parser.caps_parser import CapsParser
from gst_trace_cli.parser.element_pads_parser import ElementPadsParser
from gst_trace_cli.registry.gst_registry import GstRegistry
from gst_trace_cli.utils.log_reader import LogReader


class GstDebugTracerCli:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.line_parser = GstLogLineParser()
        self.registry = GstRegistry()
        self.parsers = [ElementPadsParser(), CapsParser(verbose=verbose)]

    def parse_file(self, path: str) -> GstRegistry:
        reader = LogReader(path)
        for raw in reader.lines():
            line = self.line_parser.parse(raw)
            if line is None:
                continue
            for p in self.parsers:
                p.handle(line, self.registry)
        self.registry.finalize()
        return self.registry


def print_registry(registry: GstRegistry, element_filter: str | None = None) -> None:
    groups: dict[tuple[str, str], list] = {}
    group_first_ts: dict[tuple[str, str], float] = {}

    for ev in registry.events:
        src_el, sink_el = ev.link_key
        if element_filter and element_filter not in (src_el, sink_el):
            continue
        groups.setdefault(ev.link_key, []).append(ev)
        group_first_ts[ev.link_key] = min(group_first_ts.get(ev.link_key, ev.ts), ev.ts)

    for link_key in sorted(groups.keys(), key=lambda k: (group_first_ts.get(k, 0.0), k[0], k[1])):
        src_el, sink_el = link_key
        if sink_el == "UNKNOWN":
            continue
        try:
            print("=" * 50)
            print(f"{src_el}  --->  {sink_el}")
            print("=" * 50)
            print("")

            events = sorted(groups[link_key], key=lambda e: (e.ts, e.order))
            for ev in events:
                ts_str = f"{ev.ts:.6f}"
                print(f"[{ts_str}] {ev.title()}")
                for l in ev.lines():
                    print(l)
                print("")
        except BrokenPipeError:
            return


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gst-trace-cli")
    ap.add_argument("log_file")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--element", default=None)
    ap.add_argument("--show-unknown", action="store_true")
    args = ap.parse_args(argv)

    cli = GstDebugTracerCli(verbose=args.verbose)
    registry = cli.parse_file(args.log_file)
    if args.show_unknown:
        print_registry_with_unknown(registry, element_filter=args.element)
    else:
        print_registry(registry, element_filter=args.element)
    return 0


def print_registry_with_unknown(registry: GstRegistry, element_filter: str | None = None) -> None:
    groups: dict[tuple[str, str], list] = {}
    group_first_ts: dict[tuple[str, str], float] = {}

    for ev in registry.events:
        src_el, sink_el = ev.link_key
        if element_filter and element_filter not in (src_el, sink_el):
            continue
        groups.setdefault(ev.link_key, []).append(ev)
        group_first_ts[ev.link_key] = min(group_first_ts.get(ev.link_key, ev.ts), ev.ts)

    for link_key in sorted(groups.keys(), key=lambda k: (group_first_ts.get(k, 0.0), k[0], k[1])):
        src_el, sink_el = link_key
        try:
            print("=" * 50)
            print(f"{src_el}  --->  {sink_el}")
            print("=" * 50)
            print("")

            events = sorted(groups[link_key], key=lambda e: (e.ts, e.order))
            for ev in events:
                ts_str = f"{ev.ts:.6f}"
                print(f"[{ts_str}] {ev.title()}")
                for l in ev.lines():
                    print(l)
                print("")
        except BrokenPipeError:
            return


if __name__ == "__main__":
    raise SystemExit(main())
