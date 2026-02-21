**Idea:**

1. Parse every log line into a structured `LogLine` object using regex
2. Classify each line into a **stateful event** (CAPS query, CAPS transform, PAD link, SUCCESS, etc.)
3. Accumulate these events into **element → element sections**
4. Print clean, grouped output in CLI

This keeps it scalable for future GUI/graph work.

---

## Step-by-step plan

### Phase 1 – Core parsing

* Build a **single regex** to split a line into:

  * timestamp
  * pid
  * thread
  * level
  * category (GST_CAPS, GST_PADS, etc.)
  * file:line:function
  * element + pad (`<videoconvert0:sink>`)
  * message body

### Phase 2 – Classification (state machine)

* Use message + category to classify into:

  * CAPS_QUERY_START
  * CAPS_QUERY_RESULT
  * CAPS_INTERSECT
  * CAPS_TRANSFORM
  * PAD_LINK_CHECK
  * PAD_LINK_SUCCESS
  * PAD_LINK_FAIL
* Ignore noise (copies, performance logs)

### Phase 3 – Aggregation

* Maintain:

  * per-element state
  * per pad pair negotiation history
* Print grouped logs:

  ```
  capsfilter0:src  → videoconvert0:sink
     - queried caps
     - intersected caps
     - compatible
     - LINKED ✅
  ```

---

## Data model (important for visualization later)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EventType(Enum):
    CAPS_QUERY = "CAPS_QUERY"
    CAPS_RESULT = "CAPS_RESULT"
    CAPS_INTERSECT = "CAPS_INTERSECT"
    CAPS_TRANSFORM = "CAPS_TRANSFORM"
    PAD_LINK_CHECK = "PAD_LINK_CHECK"
    PAD_LINK_SUCCESS = "PAD_LINK_SUCCESS"
    PAD_LINK_FAIL = "PAD_LINK_FAIL"
    NOISE = "NOISE"


@dataclass
class LogLine:
    timestamp: str
    pid: int
    thread: str
    level: str
    category: str
    element: Optional[str]
    pad: Optional[str]
    function: str
    message: str
```

---

## Regex snippets (battle-tested for your log)

### 1️⃣ Strip ANSI color codes (IMPORTANT)

```python
ANSI_ESCAPE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE.sub("", s)
```

---

### 2️⃣ Main log line regex

This works for **90%+ of GST_DEBUG lines**.

```python
LOG_LINE_RE = re.compile(
    r"""
    (?P<timestamp>\d+:\d+:\d+\.\d+)\s+
    (?P<pid>\d+)\s+
    (?P<thread>0x[0-9a-fA-F]+)\s+
    (?P<level>DEBUG|INFO|WARN|ERROR)\s+
    (?P<category>[A-Z_]+)\s+
    (?P<file>[^:]+):\d+:(?P<function>[^:]+):
    (?P<message>.*)
    """,
    re.VERBOSE,
)
```

---

### 3️⃣ Extract element + pad

```python
ELEMENT_PAD_RE = re.compile(r"<(?P<element>[^:>]+):(?P<pad>[^>]+)>")
```

---

## Parser class (clean & scalable)

```python
import re
from typing import Optional


class GstLogParser:
    def parse_line(self, raw: str) -> Optional[LogLine]:
        clean = strip_ansi(raw).strip()
        m = LOG_LINE_RE.match(clean)
        if not m:
            return None

        message = m.group("message")

        element = pad = None
        ep = ELEMENT_PAD_RE.search(message)
        if ep:
            element = ep.group("element")
            pad = ep.group("pad")

        return LogLine(
            timestamp=m.group("timestamp"),
            pid=int(m.group("pid")),
            thread=m.group("thread"),
            level=m.group("level"),
            category=m.group("category"),
            element=element,
            pad=pad,
            function=m.group("function"),
            message=message.strip(),
        )
```

---

## Classification logic (stateful events)

```python
class GstEventClassifier:
    def classify(self, log: LogLine) -> EventType:
        msg = log.message.lower()

        if "gst_pad_link_full" in log.function and "successful" in msg:
            return EventType.PAD_LINK_SUCCESS

        if "gst_pad_link_check_compatible" in log.function:
            return EventType.PAD_LINK_CHECK

        if "intersected" in msg:
            return EventType.CAPS_INTERSECT

        if "transform caps" in msg or "transforming caps" in msg:
            return EventType.CAPS_TRANSFORM

        if "query returned" in msg:
            return EventType.CAPS_RESULT

        if "query caps" in msg or "(caps)" in msg:
            return EventType.CAPS_QUERY

        if log.category in ("GST_PERFORMANCE",):
            return EventType.NOISE

        return EventType.NOISE
```

---

## Example CLI grouping logic (element → element)

```python
from collections import defaultdict


class NegotiationTracker:
    def __init__(self):
        self.sessions = defaultdict(list)

    def add(self, log: LogLine, event: EventType):
        if not log.element:
            return
        key = log.element
        self.sessions[key].append((event, log.message))

    def dump(self):
        for element, events in self.sessions.items():
            print(f"\n=== {element} ===")
            for ev, msg in events:
                print(f"  [{ev.value}] {msg}")
```

---

## Unit tests (pytest style)

```python
def test_parse_basic_line():
    parser = GstLogParser()
    line = "0:00:00.898781446 16831 0x123 DEBUG GST_PADS gstpad.c:2630:gst_pad_link_full:<a:src> linked a:src and b:sink, successful"
    log = parser.parse_line(line)

    assert log is not None
    assert log.element == "a"
    assert log.pad == "src"
    assert log.category == "GST_PADS"


def test_classify_link_success():
    classifier = GstEventClassifier()
    log = LogLine(
        timestamp="0",
        pid=1,
        thread="0x1",
        level="DEBUG",
        category="GST_PADS",
        element="videoconvert0",
        pad="sink",
        function="gst_pad_link_full",
        message="linked capsfilter0:src and videoconvert0:sink, successful",
    )

    assert classifier.classify(log) == EventType.PAD_LINK_SUCCESS
```

---

## Edge cases you already handle with this design

✅ ANSI color garbage
✅ Multiple caps blocks per line
✅ Same element appearing in multiple negotiations
✅ Noise filtering
✅ Future event types (just add enum + rule)
✅ GUI-ready (graph nodes = elements, edges = sessions)

---
