# Brain Viz — Memory Constellation

A self-contained 3-D visualization of the AI memory brain at work. Runs with
no build step: open `index.html` directly in a browser (or serve it with any
static file server to avoid CORS on the JSON fetch).

---

## Run command

```bash
# Option A — zero-install, works in any modern browser
open brain/viz/index.html          # macOS
xdg-open brain/viz/index.html     # Linux

# Option B — serve locally (avoids fetch() CORS on some browsers)
cd brain/viz
python3 -m http.server 5555
# then open  http://localhost:5555
```

No npm. No build. Three.js is loaded from CDN via an `<importmap>`.

---

## What you see

| Behaviour | Visual |
|-----------|--------|
| **INGEST** | New fact nodes fly in from above and spring-settle into their namespace cluster. A burst of particles marks landing. |
| **FORGET** | Nodes fade and drop away; a red particle burst marks deletion. |
| **RECALL** | All non-recalled nodes dim. Matching facts glow and pulse; connecting lines form a star pattern from their centroid. |

**Controls**

- **Play / Pause** — auto-advance through the event timeline.
- **Step ▶|** — advance one event at a time.
- **Context Budget slider** — live-adjusts how many recalled facts remain lit
  during a recall event. Drag it while a RECALL is displayed to see the
  budget-based selection change in real time.

Hover any node to see its fact card (subject / predicate / object, namespace,
confidence %, status).

---

## Data contract

### `Fact` shape

```ts
interface Fact {
  id: string;                          // unique fact ID, e.g. "f001"
  namespace: string;                   // e.g. "echo.private" | "shared.glossary" | …
  fact_type: string;                   // "convention" | "definition" | "preference"
                                       // | "context" | "decision" | "topology" | "ephemeral"
  subject: string;                     // left-hand side of the triple
  predicate: string;                   // relation
  object_text: string;                 // right-hand side
  confidence: number;                  // 0.0 … 1.0  (drives node size)
  status: "approved" | "pending" | "expired";
  created_at: string;                  // ISO-8601
  expires_at: string | null;           // ISO-8601 or null
}
```

### `Event` shape

```ts
interface Event {
  event_id: string;                    // unique event ID, e.g. "e001"
  event_type: "ingest" | "forget" | "recall";
  title: string;                       // short display title
  event_text: string;                  // human-readable narrative
  event_time: string;                  // ISO-8601 — used for timeline ordering
  refs: string[];                      // fact IDs this event acts on
}
```

### Top-level data file

```ts
interface BrainData {
  facts: Fact[];
  events: Event[];
}
```

---

## The live-data seam

Everything flows through **one async function** at the top of `index.html`:

```js
// brain/viz/index.html  — around line 95
async function loadEvents() {
  // SEAM: replace this fetch with your live orchestrator API call.
  // e.g. const res = await fetch('http://localhost:4000/api/brain/timeline');
  const res = await fetch('./sample-events.json');
  return res.json(); // must resolve to { facts: Fact[], events: Event[] }
}
```

To wire it to the live brain:

1. Replace the `fetch('./sample-events.json')` line with a call to the
   orchestrator's `/api/brain/timeline` endpoint (or equivalent).
2. If the API returns facts and events in separate endpoints, fetch both in
   parallel and assemble `{ facts, events }`.
3. The orchestrator's **retrieve** action maps to `event_type: "recall"`;
   **ingest** maps to `"ingest"`; **expire/forget** maps to `"forget"`.
4. The `refs` array should list the fact IDs the action touched.

No other changes are needed — the visualization reads only the `BrainData`
shape above.

---

## Namespace → color mapping

Colours are defined in `NS_COLORS` (also near the top of `index.html`):

| Namespace | Colour |
|-----------|--------|
| `echo.private` | Coral red `#ff6b6b` |
| `shared.code-conventions` | Amber `#ffd166` |
| `shared.glossary` | Teal `#06d6a0` |
| `skippy.private` | Violet `#a78bfa` |
| `devices` | Sky blue `#38bdf8` |

Add extra namespaces by extending `NS_COLORS` and `NS_CLUSTERS` in the script.

---

## File tree

```
brain/viz/
├── index.html          # entire visualization (Three.js via importmap CDN)
├── sample-events.json  # 25 facts + 20 events — the demo story
└── README.md           # this file
```

---

## Dependencies

| Library | How loaded | Version |
|---------|------------|---------|
| [Three.js](https://threejs.org) | CDN importmap (no install) | 0.165.0 |
| OrbitControls | Three.js extras (same CDN) | bundled |

No package.json needed. If CDN access is unavailable, download
`three.module.js` and `OrbitControls.js` locally and update the importmap
paths.
