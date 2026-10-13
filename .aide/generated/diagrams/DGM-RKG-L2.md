---
uid:
key: DGM-RKG-L2
type: diagram-view
group: derived
status: completed
revision: 2
scope: system
system: SYS-RKG
non_normative: true
hand_written: true
derived_from: [CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, CMP-RKG-CONVERSATION]
---

> Bootstrap view viết tay. Khi sơ đồ và CMP normative bất đồng, CMP thắng; thay file
> này bằng output generator và bỏ `hand_written` khi generator sẵn sàng.

# L2 component interaction

```mermaid
flowchart LR
    W[CMP-RKG-WEB] -->|API v1; polling / bounded turn| T[CMP-RKG-TRANSPORT]
    T -->|start job| A[CMP-RKG-ANALYZER]
    A -->|FactBatch; no DB write| G[CMP-RKG-GRAPH]
    T -->|search / traversal / context| G
    T -->|conversation command| C[CMP-RKG-CONVERSATION]
    C -->|pinned retrieval + turn/state persistence via storage façade| G
    G -->|atomic snapshot + operational state| K[(Kùzu)]
```

Single application process owns Kùzu writes in the MVP. Analyzer never imports or
executes repository source; Web never owns authoritative graph/history state.

