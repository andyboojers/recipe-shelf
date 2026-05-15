# ADR 002: Use FastAPI and Python for the Backend

## Context
The application requires a robust API backend to coordinate:
1. Receiving base64 encoded images from the frontend.
2. Interfacing with Google Generative AI for multimodal inference.
3. Managing local SQLite database transactions.
4. Uploading assets to Google Drive via OAuth.

## Decision
We decided to use **Python** as the primary backend language and **FastAPI** as the web framework.

## Consequences

### Positive
*   **AI/ML Ecosystem**: Python possesses the most mature and well-supported SDKs for AI integration (e.g., `google-generativeai`, `Pillow` for image processing).
*   **High Performance**: FastAPI is built on Starlette and Pydantic, offering excellent asynchronous request handling and automatic data validation.
*   **Developer Experience**: Automatic generation of OpenAPI (Swagger) documentation drastically speeds up API testing and frontend integration.

### Negative
*   **Environment Management**: Python requires strict virtual environment (`venv`) management to avoid dependency conflicts.
*   **Deployment Complexity**: Running Uvicorn in production requires setting up a reverse proxy (like Nginx or Caddy) and process managers.
