# ADR 001: Use React and Vite for the Frontend

## Context
The application requires a fast, responsive user interface to handle complex state machines, specifically the multi-step recipe extraction flow (uploading, selecting recipes, selecting images, and editing drafts). 
The UI needs to be component-driven to maintain code quality, and the development environment must be exceptionally fast for rapid iteration.

## Decision
We decided to use **React** as the frontend view library and **Vite** as the build tool and development server.

## Consequences

### Positive
*   **Fast Iteration**: Vite provides near-instantaneous Hot Module Replacement (HMR).
*   **Component Ecosystem**: React allows for creating encapsulated, reusable UI components (e.g., `DraftEditor`, `ImageSelector`).
*   **Easy Integration**: Vite makes it trivial to configure a development proxy to route API requests to the local backend.

### Negative
*   **Tooling Overhead**: Requires managing `npm` dependencies, a build step, and JavaScript ecosystem tooling.
*   **Client-Side Rendering**: SEO is not an immediate concern for this MVP, but traditional CSR means the initial page load must download the JavaScript bundle before rendering content.
