# State Management

This document details global state stores, persist configuration, and user preference storage.

---

## 1. Zustand Global Store

Global state is managed using a **Zustand** store inside `src/store/useSearchStore.ts`. It manages:

*   **Search Filters**:
    *   `searchQuery` (string)
    *   `searchMode` (fast, balanced, accurate)
    *   `modality` (ALL, TEXT, AUDIO, VIDEO)
    *   `topK` (number)
    *   `minScore` (number)
*   **Search History**:
    *   `searchHistory`: Array of queries containing timestamps and result counts.
*   **Theme Preferences**:
    *   `theme` (dark, light)
*   **Recent Assets Ingest Queue**:
    *   `recentAssets`: Tracks uploaded files and status updates.

---

## 2. Persistence Configuration

Zustand uses `persist` middleware to synchronize preferences with `localStorage`:

*   **Saves Preferences**: Prevents losing settings (themes, search history, settings sliders) on browser reloads.
*   **Applies Themes**: Toggles dark mode tailwind classes on initial document mount.
*   **Recent Queue Storage**: Retains local history of file uploads to track background indexing progress.
