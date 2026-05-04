# Architecture Decision Record: 001 - Technology Stack

## Context
The Recipe Shelf application requires the ability to ingest mobile screenshots and scanned magazine pages, perform automatic image rotation, grayscale conversion, and text extraction using Optical Character Recognition (OCR). We evaluated building the application using a full-stack Next.js environment (which we have successfully used in previous applications) versus a split architecture using Python (FastAPI) and React (Vite).

## Decision
We will use a split architecture consisting of a **FastAPI (Python) backend** and a **React + Vite frontend**, orchestrated via Docker Compose.

## Consequences

### Positive
* **Native Ecosystem for Image Processing:** Python provides native, highly supported libraries for computer vision (OpenCV) and OCR (Tesseract). This prevents the need for complex C++ bindings or brittle shell command executions that would be required in a Node.js/Next.js environment.
* **Separation of Concerns:** Heavy CPU tasks (OCR) on the backend will not block frontend UI thread operations or delivery.

### Negative
* **Infrastructure Complexity:** We must maintain two distinct codebases (Python and JavaScript) and orchestrate their communication using Docker Compose and a reverse proxy, rather than having a single unified full-stack server.
