# Chunking Strategy & Segmentation Rules

This document outlines the segmentation rules applied to split media assets into chunks suitable for high-dimensional semantic search.

---

## 1. Document Text Chunking

Text blocks from TXT or PDF documents are processed using character-based sliding window parameters:
*   **Chunk Window Size**: 500 characters.
*   **Sliding Window Overlap**: 50 characters.
*   **Step Size**: 450 characters (Window Size - Overlap).
*   **Timestamps**: Fixed as `NULL` (since document text lacks temporal properties).
*   **Index Tracking**: Each chunk contains a progressive `chunk_index` starting from `0`.

---

## 2. Audio Timeline Chunking

Audio tracks are partitioned into chunks to support future transcription (Whisper) and retrieval:
*   **Segment Size**: 30.0 seconds.
*   **Overlap**: None.
*   **Chunk Data Structure**:
    *   `start_time`: Index * 30.0
    *   `end_time`: min(start_time + 30.0, total_duration)
    *   `content`: Placeholder text containing time slots.

---

## 3. Video Visual Chunking

Video assets are partitioned according to temporal rules matching the frame rate extracted:
*   **Segment Size**: 2.0 seconds.
*   **Overlap**: None.
*   **Visual Mappings**: Frames captured at 2-second intervals are assigned to matching temporal chunk records.
*   **JSONB Metadata**: Every chunk includes frame index mappings and visual image file paths in its metadata property.
