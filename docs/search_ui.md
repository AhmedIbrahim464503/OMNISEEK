# Search Console UI/UX

This document details the search interface, interactive filters, result cards, and explainability widgets in the OmniSeek search dashboard.

---

## 1. Search Form & Filtering Controls

The Search portal provides granular control over the retrieval engine parameters:

*   **Query Input**: Captures search phrases and submits them via React Query.
*   **Modality Tabs**: Interactive icons filter matches (ALL, TEXT, AUDIO, VIDEO).
*   **Tuning Settings Panel**: Exposes three key parameters:
    *   *Search Strategy Profile*: Selects `Fast` (vector search only), `Balanced` (FTS + Vector), or `Accurate` (Cross-Encoder Reranking) profiles.
    *   *Top-K Limit Slider*: Modifies query chunk thresholds (5 to 50 results).
    *   *Confidence Slider*: Restricts result lists to matches satisfying minimum score criteria (0% to 90%).

---

## 2. Result Cards

Search results are rendered inside individual cards detailing the match parameters:
*   **Header**: Displays filename, modality badge, confidence score, and match strategy.
*   **Body Content**: Displays text excerpts or transcript segments.
*   **Footer**: Provides quick links:
    *   *Explain Match*: Displays semantic, keyword, and reranker score variables.
    *   *Launch Media*: Opens the Temporal Viewer, initiating playback at the matched timestamp.
*   **Temporal Badges**: Displays offset timestamps (e.g. `00:45`) for audio and video chunks.
