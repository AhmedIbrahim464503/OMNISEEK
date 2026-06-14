# Accessibility Guide (a11y)

This guide documents accessibility compliance standards and conventions implemented in the OmniSeek frontend.

---

## 1. Accessibility Compliance Standards

The interface is designed to comply with WCAG 2.1 AA guidelines, prioritizing accessibility across all components:

### A. Semantic markup hierarchy:
*   Uses HTML5 semantic elements (`<aside>`, `<main>`, `<nav>`, `<form>`).
*   Ensures a single `<h1>` per view, followed by organized `<h2>` and `<h3>` tags.

### B. Dynamic Focus Styling:
*   Applies clear, high-contrast outlines (`focus:ring-2 focus:ring-primary`) around inputs and buttons for keyboard navigation.

### C. Color Contrast:
*   Utilizes color variables mapping to high-contrast values (e.g. Indigo `#4f46e5` on slate background) to ensure visual legibility.

### D. ARIA Attribute labels:
*   Provides screen-reader descriptors and aria labels for icons and media players.
