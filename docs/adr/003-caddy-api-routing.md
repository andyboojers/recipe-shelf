# Architecture Decision Record: 003 - API Routing and Proxy Strategy

## Context
Because the FastAPI backend and React frontend run as separate services on different ports (8000 and 3004), the user's browser will inherently block frontend requests sent directly to the backend due to CORS (Cross-Origin Resource Sharing) security policies. 

## Decision
We will use a **Caddy Reverse Proxy** on the host machine to route traffic based on path. Specifically, any request to `http://recipes.local/api/*` will be proxied to the internal FastAPI backend, while all other requests will route to the React frontend.

## Consequences

### Positive
* **No CORS Configuration Needed:** The browser perceives all communication as originating from a single domain (`recipes.local`), entirely avoiding CORS restrictions.
* **Security:** The backend port (8000) does not need to be exposed directly to the outside local network, routing purely through the proxy.
* **Simplified Frontend Logic:** Frontend developers can use relative URL paths (e.g., `fetch('/api/upload')`) without managing dynamic absolute backend URLs based on environment.

### Negative
* **Dependency:** Requires Caddy configuration and limits standalone testing without a proxy running.
