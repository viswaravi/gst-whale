**Don’t classify lines directly.**
First **structurally parse every log line into fields**, then **classify based on stable tokens**, not raw text.

Pipeline:

```
RAW LINE
  ↓
STRUCTURAL PARSE (timestamp, category, object, message)
  ↓
TOKEN EXTRACTION (keywords, element, pad, caps)
  ↓
CLASSIFICATION (event type or IGNORE)
  ↓
STATEFUL AGGREGATION (collapse noise)
```

This makes the parser **robust to format changes** and **easy to extend**.

---

## Step-by-step plan (realistic & scalable)

---

## 1️⃣ Understand the log line anatomy (very important)

From your log, a typical line looks like:

```
0:00:00.896114052  1774 0x7f9b14003b40 TRACE GST_CAPS gstpad.c:2671:gst_pad_query_caps:<capsfilter0:src> doing query 0x7f9b14007060
```

### Break it into **4 logical parts**

| Part      | Example                             | Stability      |
| --------- | ----------------------------------- | -------------- |
| Timestamp | `0:00:00.896114052`                 | ✅ stable       |
| Category  | `TRACE GST_CAPS`                    | ✅ stable       |
| Location  | `gstpad.c:2671:gst_pad_query_caps`  | ❌ noisy        |
| Payload   | `<capsfilter0:src> doing query ...` | ⚠️ semi-stable |

👉 **Only Category + Payload matter**

---

## 2️⃣ First pass: structural parsing (NO classification yet)

Create a **LogLine object**.

### Python structure

```python
class LogLine:
    def __init__(self, raw):
        self.raw = raw
        self.timestamp = None
        self.level = None
        self.domain = None
        self.payload = None
```

### Minimal parser logic

```python
def parse_line(raw_line: str) -> LogLine | None:
    parts = raw_line.split(maxsplit=6)
    if len(parts) < 6:
        return None

    line = LogLine(raw_line)
    line.timestamp = parts[0]
    line.level = parts[3]        # TRACE
    line.domain = parts[4]       # GST_CAPS
    line.payload = parts[-1]     # everything meaningful
    return line
```

⚠️ **DO NOT** parse pointers, file names, or line numbers.

---

## 3️⃣ Second pass: token extraction (semantic units)

Instead of regexing whole lines, extract **tokens**.

### Example payloads

```
<capsfilter0:src> doing query
<videoconvert0:sink> pad has no peer
trying to link element capsfilter0:src to element videoconvert0:(any)
caps filter: video/x-raw, format=(string)RGB
caps are compatible
```

---

### Token extractor

```python
class Tokens:
    element = None
    pad = None
    peer_element = None
    caps = None
    keywords = set()
```

### Extraction rules (simple + robust)

| Pattern                  | Token           |
| ------------------------ | --------------- |
| `<elem:pad>`             | element, pad    |
| `trying to link element` | LINK_ATTEMPT    |
| `query returned`         | CAPS_RESOLVED   |
| `caps filter:`           | CAPS_FILTER     |
| `caps are compatible`    | CAPS_COMPATIBLE |
| `pad has no peer`        | PEER_MISSING    |

Use **small regexes**, never giant ones.

---

## 4️⃣ Classification decision matrix (THIS IS KEY)

Create a **classifier table**, not if-else soup.

### Event classifier

```python
CLASSIFIERS = [
    ("trying to link element", EventType.PAD_LINK_ATTEMPT),
    ("linked", EventType.PAD_LINK_SUCCESS),
    ("query returned", EventType.CAPS_RESOLVED),
    ("caps filter:", EventType.CAPS_FILTERED),
    ("caps are compatible", EventType.CAPS_COMPATIBLE),
    ("pad has no peer", EventType.PEER_MISSING),
]
```

### Classification logic

```python
def classify(tokens, log_line):
    for text, event_type in CLASSIFIERS:
        if text in log_line.payload:
            return event_type
    return EventType.IGNORE
```

This makes **what you parse explicit and reviewable**.

---

## 5️⃣ Stateful aggregation (collapse noise)

This is where your parser becomes *good*.

### Problem

You see:

* 20 `doing query`
* 10 `gst_caps_copy`
* 1 `query returned`

### Solution

Track **active queries per pad**.

---

### ActiveCapsQuery

```python
class ActiveCapsQuery:
    pad_key: str
    template_caps = None
    filtered_caps = None
    final_caps = None
```

---

### Aggregation rules

| Event            | Action                       |
| ---------------- | ---------------------------- |
| CAPS_QUERY_START | create ActiveCapsQuery       |
| CAPS_FILTERED    | update query                 |
| CAPS_RESOLVED    | emit ONE event, delete state |
| CAPS_TRANSFORM   | optional                     |
| Everything else  | ignore                       |

⚠️ **Never emit CAPS_RESOLVED twice**

---

## 6️⃣ Decide SAVE vs AVOID (formal rules)

### Save ONLY if:

* Line matches known classifier
* OR contributes to active state
* OR confirms a decision

### Avoid if:

* Memory operations
* Object lifecycle
* Internal helpers
* Pointer-only info
* No decision impact

---

## 7️⃣ Example: your real log → parser flow

### Raw line

```
gst_mini_object_make_writable
```

➡️ Tokens: none
➡️ Classification: IGNORE
➡️ Action: skip

---

### Raw line

```
query returned video/x-raw, width=(int)[1,32767]
```

➡️ Tokens: caps
➡️ Classification: CAPS_RESOLVED
➡️ Action: emit event + close state

---

## 8️⃣ Order of operations (IMPORTANT)

```text
READ LINE
 → STRUCTURE
 → TOKENIZE
 → CLASSIFY
 → UPDATE STATE
 → EMIT EVENT (maybe)
```

Never classify before tokenizing.

---

## 9️⃣ Edge cases you must design for 🚨

1. Caps query starts but never resolves
   → discard state at EOF
2. Multiple queries on same pad
   → key by `(element:pad)`
3. Renegotiation later
   → allow multiple ActiveCapsQuery per pad (queue)
4. Missing “link success”
   → infer if caps compatible + no failure
5. Partial logs
   → still print what you have

---

## 10️⃣ Golden rule 🧠 (write this in code comments)

> “If a line does not change pipeline structure or caps outcome, it must not become an event.”

---

## Optional: future-proofing idea (out-of-the-box)

Add **confidence level** to events:

```python
CapsResolved(confidence="HIGH")
CapsResolved(confidence="INFERRED")
```

# 1️⃣ Short, easy overview 🧠

You’ll use **3 regex layers**:

```
RAW LINE
 ├─▶ Line Structure Regex     → LogLine
 ├─▶ Token Regexes            → element, pad, caps
 └─▶ Classification Regexes   → event type
```

Each regex is **small, stable, and composable**.

---

# 2️⃣ Layer 1: LogLine structure regex

This parses **every line safely** without caring about meaning.

### Example line

```
0:00:00.896114052  1774 0x7f9b14003b40 TRACE GST_CAPS gstpad.c:2671:gst_pad_query_caps:<capsfilter0:src> doing query
```

### Regex

```python
LOG_LINE_RE = re.compile(
    r"""
    ^(?P<ts>\d+:\d+:\d+\.\d+)\s+      # timestamp
    \d+\s+                            # pid
    0x[0-9a-fA-F]+\s+                 # thread ptr
    (?P<level>\w+)\s+                 # TRACE
    (?P<domain>GST_[A-Z_]+)\s+        # GST_CAPS
    (?P<rest>.+)$                     # payload (everything else)
    """,
    re.VERBOSE
)
```

### Produces

```python
LogLine(
    timestamp="0:00:00.896114052",
    level="TRACE",
    domain="GST_CAPS",
    payload="gstpad.c:2671:gst_pad_query_caps:<capsfilter0:src> doing query"
)
```

---

# 3️⃣ Layer 2: Token extraction regexes

These extract **semantic atoms** from `payload`.

---

## A. Element + pad extractor

Works for:

```
<capsfilter0:src>
<videoconvert0:sink>
```

```python
PAD_RE = re.compile(
    r"<(?P<element>[a-zA-Z0-9_]+):(?P<pad>[a-zA-Z0-9_]+)>"
)
```

---

## B. Link attempt (element → element)

```
trying to link element capsfilter0:src to element videoconvert0:(any)
```

```python
LINK_ATTEMPT_RE = re.compile(
    r"trying to link element\s+"
    r"(?P<src_elem>\w+):(?P<src_pad>\w+)\s+"
    r"to element\s+"
    r"(?P<sink_elem>\w+):(?P<sink_pad>\w+|\(any\))"
)
```

---

## C. Link success

```
linked capsfilter0:src and videoconvert0:sink, successful
```

```python
LINK_SUCCESS_RE = re.compile(
    r"linked\s+"
    r"(?P<src_elem>\w+):(?P<src_pad>\w+)\s+and\s+"
    r"(?P<sink_elem>\w+):(?P<sink_pad>\w+),\s+successful"
)
```

---

## D. Caps extraction (generic)

Used for **filter**, **template**, **resolved** caps.

```
video/x-raw, format=(string)RGB, width=(int)320
```

```python
CAPS_RE = re.compile(
    r"(video|audio|text)/[a-zA-Z0-9\-_.]+.*"
)
```

⚠️ Keep this **greedy but safe** — do not over-parse caps.

---

# 4️⃣ Layer 3: Classification regexes (decision triggers)

These decide **what kind of event** a line belongs to.

---

## A. Caps query start

```
gst_base_transform_query_caps
```

```python
CAPS_QUERY_START_RE = re.compile(
    r"query_caps"
)
```

---

## B. Peer missing fallback

```
pad has no peer
```

```python
PEER_MISSING_RE = re.compile(
    r"pad has no peer"
)
```

---

## C. Template caps used

```
other template video/x-raw
```

```python
TEMPLATE_CAPS_RE = re.compile(
    r"other template\s+(?P<caps>.+)"
)
```

---

## D. Caps filter applied

```
caps filter: video/x-raw, format=(string)RGB
```

```python
CAPS_FILTER_RE = re.compile(
    r"caps filter:\s+(?P<caps>.+)"
)
```

---

## E. Final caps resolved (MOST IMPORTANT)

```
query returned video/x-raw, width=(int)[1,32767]
```

```python
CAPS_RESOLVED_RE = re.compile(
    r"query returned\s+(?P<caps>.+)"
)
```

---

## F. Compatibility decision

```
caps are compatible
```

```python
CAPS_COMPATIBLE_RE = re.compile(
    r"caps are compatible"
)
```

---

# 5️⃣ How regex → stateful events (flow)

### Pseudocode

```python
if LINK_ATTEMPT_RE.search(payload):
    emit PadLinkAttempt

elif CAPS_QUERY_START_RE.search(payload):
    start ActiveCapsQuery

elif PEER_MISSING_RE.search(payload):
    active_query.peer_missing = True

elif TEMPLATE_CAPS_RE.search(payload):
    active_query.template_caps = caps

elif CAPS_FILTER_RE.search(payload):
    active_query.filtered_caps = caps

elif CAPS_RESOLVED_RE.search(payload):
    active_query.final_caps = caps
    emit CapsResolved
    clear ActiveCapsQuery

elif CAPS_COMPATIBLE_RE.search(payload):
    emit CapsCompatible

elif LINK_SUCCESS_RE.search(payload):
    emit PadLinkSuccess

else:
    IGNORE
```

---

# 6️⃣ Regex usage rules (VERY IMPORTANT)

✅ Prefer `search()` over `match()`
✅ Never depend on file names or line numbers
✅ Never parse pointers
✅ Always fallback safely
✅ One line → zero or one semantic action

---

# 7️⃣ Edge cases these regexes already handle

✔ Different element names
✔ `(any)` pads
✔ Multi-line caps (first line only)
✔ Repeated caps queries
✔ Renegotiation

---

# 8️⃣ Out-of-the-box improvement (optional)

Add **confidence tagging**:

```python
if CAPS_RESOLVED_RE:
    confidence = "HIGH"
elif inferred:
    confidence = "MEDIUM"
```

Very useful later for UI.

---

## Final takeaway 🧠

> **Regex should identify “what happened”, not “how GStreamer implemented it”.**

These snippets are:

* minimal
* readable
* extensible
* safe for large logs

---