# Component Library

This guide documents the design system, structural styling conventions, and reusable widgets implemented in the OmniSeek frontend.

---

## 1. Core Visual Elements

The UI uses a dark-mode slate theme matching developer-centric dashboard visuals (inspired by OpenAI, Linear, and Vercel).

### Reusable Primitives:
*   **Navigation (`Navigation.tsx`)**: Responsive sidebar containing path routing links, active state backgrounds, and the theme switcher button.
*   **MetricCard (Dashboard)**: Grid widgets rendering statistical telemetry outputs (Asset, Chunk, Query volumes, Latencies).
*   **UploadZone (`UploadPage`)**: Interactive dropzone executing raw stream file format and sizing checks before submission.
*   **ExplainabilityPanel (`ExplainabilityPanel.tsx`)**: Statistical graphs visualizing keyword vs semantic vs reranker score totals.
*   **TemporalViewer (`MediaViewer.tsx`)**: Sub-player router hosting `VideoPlayer`, `AudioPlayer`, and `DocumentViewer` components.

---

## 2. Dynamic Component APIs

### A. ExplainabilityPanel
```typescript
interface Props {
  explanation?: SearchExplanation;
  score: number;
}
```
Renders dense linear fusion percentages and plain-text rationales.

### B. VideoPlayer & AudioPlayer
```typescript
interface PlayerProps {
  src: string;
  startTime?: number; // in seconds
}
```
Initializes standard HTML5 streams, automatically seeking to target temporal offsets.

### C. DocumentViewer
```typescript
interface DocProps {
  assetName: string;
  content: string;
  highlightText?: string;
}
```
Renders PDF or TXT fragments, wrapping matches in styled marker highlights.
