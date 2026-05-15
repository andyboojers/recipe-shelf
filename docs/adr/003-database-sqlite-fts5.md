# ADR 003: Use Raw SQLite with FTS5 for Local Database

## Context
The application requires a local datastore to cache extracted recipes, manage drafts, and support high-speed keyword searching. Because this is an MVP designed to run locally (with persistence handled by Google Drive), we need a database that does not require a separate daemon process (like PostgreSQL or MySQL).

## Decision
We decided to use **SQLite** accessed via raw SQL queries (using Python's built-in `sqlite3` module), specifically leveraging the **FTS5 (Full-Text Search)** extension.

## Consequences

### Positive
*   **Zero Configuration**: The database is a single local file (`data/recipes.db`), eliminating complex setup and administration.
*   **Performance**: FTS5 provides lightning-fast search capabilities across recipe text, ingredients, and tags without needing external search engines like Elasticsearch.
*   **Simplicity**: Using raw SQL rather than a heavy ORM (like SQLAlchemy) keeps the backend exceptionally lightweight and easy to debug.

### Negative
*   **Schema Migrations**: Without an ORM or migration tool (like Alembic), schema changes are difficult and currently require wiping the local development database file to rebuild tables.
*   **Concurrency**: SQLite handles concurrent reads well, but concurrent writes lock the entire database file. This is acceptable for a single-user MVP but will not scale well in a multi-user environment.
