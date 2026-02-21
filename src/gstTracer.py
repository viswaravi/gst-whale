from __future__ import annotations

import argparse
from typing import Optional

from parser.base_parser import GstLogLineParser
from registry.gst_registry import GstRegistry
from utils.log_reader import LogReader


def print_processing_stats(registry: GstRegistry, element_filter: Optional[str] = None) -> None:
    """Print processing time statistics for elements."""
    stats = registry.get_all_processing_stats()
    
    if not stats:
        print("No processing time data found.")
        return
    
    print("\n" + "=" * 60)
    print("PROCESSING TIME STATISTICS")
    print("=" * 60)
    
    for element_name, element_stats in sorted(stats.items()):
        if element_filter and element_filter not in element_name:
            continue
            
        print(f"\nElement: {element_name}")
        print(f"  Count:     {element_stats['count']}")
        print(f"  Total:     {element_stats['total']*1000:.3f}ms")
        print(f"  Average:   {element_stats['avg']*1000:.3f}ms")
        print(f"  Min:       {element_stats['min']*1000:.3f}ms")
        print(f"  Max:       {element_stats['max']*1000:.3f}ms")


def print_shark_events(registry: GstRegistry, element_filter: Optional[str] = None, tracer_type: Optional[str] = None) -> None:
    """Print shark tracer events."""
    events = registry.shark_events
    
    if not events:
        print("No shark tracer events found.")
        return
    
    # Filter events
    filtered_events = []
    for event in events:
        if element_filter and element_filter not in event.element_name:
            continue
        if tracer_type and event.tracer_type != tracer_type:
            continue
        filtered_events.append(event)
    
    if not filtered_events:
        print("No events match the specified filters.")
        return
    
    print("\n" + "=" * 60)
    print("SHARK TRACER EVENTS")
    print("=" * 60)
    
    for event in sorted(filtered_events, key=lambda e: (e.ts, e.order)):
        print(f"\n{event.ts:.6f} - {event.title()}")
        for line in event.lines():
            print(line)


def print_debug_events(registry: GstRegistry, element_filter: Optional[str] = None) -> None:
    """Print debug events (caps negotiation, pad linking)."""
    events = [ev for ev in registry.events if not hasattr(ev, 'tracer_type')]
    
    if not events:
        print("No debug events found.")
        return
    
    # Filter events
    filtered_events = []
    for event in events:
        if element_filter:
            src_el, sink_el = event.link_key
            if element_filter not in (src_el, sink_el):
                continue
        filtered_events.append(event)
    
    if not filtered_events:
        print("No events match the specified filter.")
        return
    
    print("\n" + "=" * 60)
    print("DEBUG EVENTS")
    print("=" * 60)
    
    # Group events by link
    groups = {}
    for ev in filtered_events:
        groups.setdefault(ev.link_key, []).append(ev)
    
    for link_key in sorted(groups.keys(), key=lambda k: (min(e.ts for e in groups[k]), k[0], k[1])):
        src_el, sink_el = link_key
        if sink_el == "UNKNOWN":
            continue
        
        print(f"\n{src_el}  --->  {sink_el}")
        print("-" * 50)
        
        for ev in sorted(groups[link_key], key=lambda e: e.ts):
            print(f"{ev.ts:.6f} - {ev.title()}")
            for line in ev.lines():
                print(f"  {line}")


def print_summary(registry: GstRegistry) -> None:
    """Print a summary of all parsed data."""
    print("\n" + "=" * 60)
    print("PARSING SUMMARY")
    print("=" * 60)
    
    print(f"Elements found: {len(registry.elements)}")
    print(f"Pads found: {len(registry.pads)}")
    print(f"Links found: {len(registry.links)}")
    print(f"Debug events: {len([e for e in registry.events if not hasattr(e, 'tracer_type')])}")
    print(f"Shark tracer events: {len(registry.shark_events)}")
    
    # Show elements with processing time data
    elements_with_proctime = len(registry.element_processing_times)
    if elements_with_proctime > 0:
        print(f"Elements with processing time data: {elements_with_proctime}")
        
        print("\nElements with processing time stats:")
        for element_name in sorted(registry.element_processing_times.keys()):
            stats = registry.get_element_processing_stats(element_name)
            if stats:
                print(f"  {element_name}: {stats['count']} samples, avg {stats['avg']*1000:.3f}ms")


def main():
    parser = argparse.ArgumentParser(description="Parse GStreamer debug and shark tracer logs")
    parser.add_argument("log_file", help="Path to the log file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-e", "--element", help="Filter by element name")
    parser.add_argument("-t", "--tracer-type", help="Filter by tracer type (e.g., proctime)")
    parser.add_argument("--enable-debug", action="store_true", default=True, help="Enable debug parsing (default: enabled)")
    parser.add_argument("--disable-debug", action="store_true", help="Disable debug parsing")
    parser.add_argument("--enable-tracer", action="store_true", default=True, help="Enable tracer parsing (default: enabled)")
    parser.add_argument("--disable-tracer", action="store_true", help="Disable tracer parsing")
    parser.add_argument("--debug-only", action="store_true", help="Parse only debug lines")
    parser.add_argument("--tracer-only", action="store_true", help="Parse only tracer lines")
    parser.add_argument("--stats", action="store_true", help="Show processing time statistics")
    parser.add_argument("--shark-events", action="store_true", help="Show shark tracer events")
    parser.add_argument("--debug-events", action="store_true", help="Show debug events")
    parser.add_argument("--summary", action="store_true", help="Show parsing summary")
    
    args = parser.parse_args()
    
    # Handle conflicting flags
    if args.debug_only and args.tracer_only:
        print("Error: --debug-only and --tracer-only cannot be used together")
        return 1
    
    # Determine which parsers to enable
    enable_debug = args.enable_debug and not args.disable_debug and not args.tracer_only
    enable_tracer = args.enable_tracer and not args.disable_tracer and not args.debug_only
    
    # Create shared objects
    line_parser = GstLogLineParser()
    registry = GstRegistry()
    reader = LogReader(args.log_file)
    
    # Process file line by line
    for raw_line in reader.lines():
        log_line = line_parser.parse(raw_line)
        if log_line is None:
            continue
        
        # Route based on domain and enabled flags
        if log_line.domain == "GST_DEBUG" and enable_debug:
            from debugTracer import parse_debug_line
            parse_debug_line(log_line, registry, args.verbose)
        elif log_line.domain == "GST_TRACER" and enable_tracer:
            from sharkTracer import parse_tracer_line
            parse_tracer_line(log_line, registry, args.verbose)
    
    registry.finalize()
    
    # If no specific output requested, show summary
    if not any([args.stats, args.shark_events, args.debug_events, args.summary]):
        args.summary = True
    
    # Output results
    if args.summary:
        print_summary(registry)
    
    if args.stats:
        print_processing_stats(registry, args.element)
    
    if args.shark_events:
        print_shark_events(registry, args.element, args.tracer_type)
    
    if args.debug_events:
        print_debug_events(registry, args.element)
    
    return 0


if __name__ == "__main__":
    exit(main())
