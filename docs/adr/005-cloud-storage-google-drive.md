# ADR 005: Use Google Drive for Recipe Storage

## Context
The application needs to persistently store structured recipe data (JSON) and cropped food photos (JPEG). However, a key requirement of the MVP is to avoid relying on a dedicated, paid cloud database while ensuring the user's data remains accessible, portable, and secure outside of the application itself.

## Decision
We decided to use **Google Drive** via the Google Drive API as the permanent cloud storage layer. The application saves recipes as discrete `.json` files and photos as `.jpg` files within a dedicated "Recipe Shelf" Drive folder.

## Consequences

### Positive
*   **User Ownership**: The user retains full control and ownership of their raw recipe data files.
*   **No Hosting Costs**: Leverages the user's existing Google account storage limit, entirely avoiding cloud database hosting fees for the developer.
*   **Portability**: The JSON format is universally readable and easily exportable.

### Negative
*   **Latency**: Saving or retrieving individual files from Google Drive is significantly slower than querying a traditional database. To mitigate this, a local SQLite cache is required.
*   **OAuth Complexity**: Requires setting up Google Cloud Platform credentials, managing OAuth consent screens, and securely storing refresh tokens locally.
