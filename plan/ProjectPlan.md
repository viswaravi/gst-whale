*(CLI-first GStreamer Trace Visualizer – Sectioned Logging)*

---

## 🎯 Goal

Implement the **first working version** of a **Python-based GStreamer trace parser** that:

* Reads a `GST_DEBUG` `.log` file
* Parses **element-to-element interactions**
* Logs **collapsed, meaningful events** to the **command line**
* Groups output by **(element → element)** sections
* Is **stateful**, **robust**, and **scalable**
* Does **NOT** implement GUI or graph yet

The output must be **human-readable and debugger-friendly**.

---

## 🧠 Mental Model (IMPORTANT)

The log contains **massive noise**.
The program must **collapse dozens of lines into a few semantic events**.

We care about:

* Element linking attempts
* Caps negotiation (start → filter → resolve)
* Compatibility decision
* Link success / failure

Everything else is **skipped**.

---

## 🧱 Architecture Requirements

### Use clean, scalable structure:

```
gst_trace_cli/
├── parser/
│   ├── base_parser.py
│   ├── element_pads_parser.py
│   ├── caps_parser.py
│
├── model/
│   ├── element.py
│   ├── pad.py
│   ├── events.py
│
├── registry/
│   └── gst_registry.py
│
├── utils/
│   └── log_reader.py
│
└── main.py
```

Use **classes and member functions only** (no script-style parsing).

---

## 🧩 Core Data Structures

### GstRegistry (central store)

Must store:

* Elements
* Pads
* Links
* Collapsed events (timeline)
* Temporary parsing state (active caps queries)

```python
class GstRegistry:
    elements: dict[str, GstElement]
    pads: dict[str, GstPad]
    links: set[tuple[GstPad, GstPad]]
    events: list[GstEvent]

    # parsing-only state
    active_caps_queries: dict[str, ActiveCapsQuery]
```

---

## 🧾 Event Types (minimal set)

Define clear event classes (dataclasses preferred):

* `PadLinkAttempt`
* `CapsQueryStart`
* `CapsTemplateUsed`
* `CapsFiltered`
* `CapsResolved`
* `CapsCompatible`
* `PadLinkSuccess`
* `PadLinkFailure`

Each event MUST:

* store timestamp
* store involved elements/pads
* store raw caps string (if applicable)

---

## 🧠 Stateful Parsing (CRITICAL)

### Caps negotiation MUST be parsed as a **state machine**

Example:

* Start on: `gst_base_transform_query_caps`
* Track:

  * peer missing fallback
  * template caps
  * transformed caps
* Emit **ONLY ONE `CapsResolved` event**
* Discard intermediate noise

Do NOT emit events per line.

---

## 🪵 What to Parse (STRICT)

### Parse ONLY these patterns:

#### Element linking

```
trying to link element A:src to element B:sink
linked A:src and B:sink, successful
```

#### Caps resolution

```
query returned video/x-raw,...
caps filter:
caps are compatible
```

#### Template fallback

```
pad has no peer
other template video/x-raw
```

### Skip everything else:

* memory ops
* object copies
* internal helpers
* file:line info
* pointer addresses

---

## 🖨️ CLI OUTPUT FORMAT (VERY IMPORTANT)

### Group output by **element → element**

Example:

```
==================================================
capsfilter0  --->  videoconvert0
==================================================

[0.896114] LINK ATTEMPT
  capsfilter0:src → videoconvert0:sink

[0.896272] CAPS QUERY START
  Target pad: videoconvert0:sink
  Reason: peer missing → template fallback

[0.896381] TEMPLATE CAPS
  video/x-raw, format=(string){...}

[0.898444] FINAL CAPS
  video/x-raw, format=RGB, width=320, height=240

[0.898747] CAPS COMPATIBLE

[0.898781] LINK SUCCESS
```

### Rules:

* Each section = ONE element pair
* Events must be **time-ordered**
* Output must be deterministic
* Easy to visually scan

---

## 🧪 Edge Cases to Handle

The implementation MUST handle:

* Multiple caps queries for same pad
* Caps renegotiation later in pipeline
* Missing “link success” lines (infer success if caps resolved)
* Partial logs
* Multiple pads per element
* Repeated link attempts

No crashes allowed due to malformed lines.

---

## 🚦 Scope Control

DO:

* CLI output only
* Clean class-based design
* Clear separation of parsing vs printing

DO NOT:

* Implement GUI
* Use Graphviz
* Over-optimize
* Parse every log line

---

## 🧠 Design Philosophy (Follow This)

> “Parse decisions, not mechanics.”
> “One caps query → one CapsResolved event.”
> “One link → one graph edge.”

---

## ✅ Deliverables

The final program must:

1. Accept a `.log` file path
2. Parse it safely
3. Print grouped element-to-element sections
4. Show collapsed, meaningful events only
5. Be easy to extend later for GUI / graph

---

## 🧩 Bonus (Optional if easy)

* `--verbose` flag to show extra caps transform steps
* `--element capsfilter0` filter
* Colored output using `rich` (optional)

---

## 🏁 End Goal

This CLI output should already feel like a **debugging superpower**.

Once this is solid, the same registry will power:

* graph visualization
* timeline UI
* interactive inspection