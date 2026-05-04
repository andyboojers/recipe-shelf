# Architecture Decision Record: 004 - Unsaved Draft Storage

## Context
When a user uploads an image/scan, it is immediately processed through OCR to generate a draft. This draft remains uncommitted until the user reviews, corrects, and explicitly "saves" it to Google Drive. We need a strategy for storing this temporary data.

## Decision
We will store temporary draft metadata (extracted text, parsed fields) within the local **SQLite** database. The corresponding temporary images will be saved directly to a local Docker volume mapped to `/data/drafts`.

## Consequences

### Positive
* **Prevents Upstream Clutter:** Google Drive is kept clean and only contains finalized, user-approved recipes.
* **Fast Interactions:** Saving and editing drafts is extremely fast as it occurs purely on the local disk.

### Negative
* **State Management:** Drafts are stranded on the local server. If the server is destroyed before a draft is saved to Google Drive, the draft is lost.
* **Garbage Collection Required:** We will eventually need a background mechanism to clean up abandoned files in `/data/drafts` to prevent indefinite disk consumption.
