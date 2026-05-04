# Architecture Decision Record: 002 - Primary Data Storage Strategy

## Context
We need a robust storage solution to store the actual recipe images, thumbnails, and structured recipe data (JSON manifests). The system needs to be accessible on a local home network but resilient against local hardware failures without requiring complex backup strategies for the MVP.

## Decision
We will use **Google Drive** as the definitive source of truth and long-term storage, coupled with a local **SQLite database** acting purely as a searchable cache.

## Consequences

### Positive
* **Resilience & Versioning:** Google Drive automatically provides durability, backups, and version history.
* **MVP Scope Reduction:** We do not need to build export features, backup zip functionality, or complex disaster recovery protocols into the MVP application.
* **Portability:** The user retains full ownership and easy access to their raw files outside the application ecosystem.

### Negative
* **Network Dependency:** The application relies on Google Drive API availability. If offline, the app must operate in a degraded mode using only the local SQLite cache.
* **Sync Complexity:** A background job must be maintained to keep the local SQLite Full-Text Search (FTS5) index in sync with upstream Google Drive changes.
