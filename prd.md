# SPEC-001-App-Solution-Design

## Background

The app helps a home user digitize and manage recipes found in printed magazines. The user scans magazine pages containing recipes, and the app extracts recipe text and images from the scans, organizes the resulting recipe dataset, and makes it searchable by keywords.

The main problem is that many recipes are currently scattered across physical magazines, making them difficult to access, search, and reuse. The app should make these recipes available to devices on the user's local home network.

## Requirements

### Must Have

* The system must display original scan images alongside extracted recipe data for verification.

* The system must allow uploading images captured as mobile screenshots in addition to scanned pages.

* The system must correctly process screenshots (including cropping/orientation handling) through the same OCR and parsing pipeline.

* The system must allow a single home user to upload scanned magazine recipe pages, assuming one recipe per uploaded image or scan for the MVP.

* The system must extract recipe text from scanned images using OCR.

* The system must preserve or extract relevant recipe images from the scan.

* The system must organize each recipe as a structured record with at least title, ingredients, instructions, source scan, images, and searchable text.

* The system must automatically suggest tags from recipe text.

* The system must identify recipe sections such as ingredients, method, servings, cooking time, and notes.

* The system must support favorites or personal notes, even without separate user accounts.

* The system must provide keyword search across recipe titles, ingredients, instructions, and OCR text.

* The system must be accessible from phones, tablets, and laptops on the user's local home network.

* The MVP must not require cloud hosting for the application runtime, though it may depend on Google Drive for recipe data storage and retrieval.

### Should Have

* The system should create a recipe draft after OCR and allow manual review/correction before the recipe is saved to the searchable library.
* The system should allow basic tagging, such as cuisine, meal type, ingredient, or magazine/source.
* The system should support uploading scans from a phone or desktop browser.

### Could Have

* The system could later support splitting pages that contain multiple recipes, but this is out of scope for the MVP.

### Won't Have in MVP

* Multi-user accounts or household profiles.
* Public internet access outside the home network (except Google Drive integration).
* Cloud OCR as a hard dependency.
* Meal planning, grocery lists, or nutrition analysis unless added later.

### Clarification on Backup Strategy

Explicit export/backup features are not required in the MVP because Google Drive acts as the canonical and resilient storage layer. All recipe data (JSON manifests and images) is already stored durably in Google Drive, which provides version history and redundancy.

Optional export features (e.g., ZIP export) could still be added later for portability, but are not necessary for resilience in this design.

## Implementation

### Overview

Single-node Docker Compose app on a Linux host.

* Google Drive = source of truth
* SQLite = local cache + search index (rebuildable)
* Heuristic parsing + manual correction UI

### Services

* Backend (FastAPI): API, OCR orchestration, parsing, tagging, Drive integration
* Frontend (React + Vite): upload, crop, edit, search, view

### Core API Endpoints

* POST /upload → Upload image (scan/screenshot) → returns draft id
* GET /drafts/{id} → OCR + parsed draft
* POST /recipes → Save to Google Drive (create/overwrite recipe.json + files)
* PUT /recipes/{id} → Update recipe (overwrite recipe.json)
* GET /recipes?q=... → Search via SQLite FTS5
* GET /recipes/{id} → Metadata from cache
* GET /files/{drive_file_id} → Image proxy (cache → Drive)

### Image Processing + OCR

Pipeline:

1. Manual crop (frontend, required for screenshots). Frontend sends the already-cropped image to the backend.
2. Auto-rotate (EXIF)
3. Convert to grayscale
4. Light contrast/denoise (OpenCV)
5. OCR (Tesseract, --psm 6)

Note: Processed images are used only for OCR. Original color images are stored and displayed.

### Parsing (Heuristics)

* Title: first/most prominent line
* Ingredients: lines matching quantity/unit regex
* Steps: numbered lines or paragraphs
* Time/Servings: regex (min/hr/serves)
* Notes: remainder

### Tag Suggestion

* Tokenize title + ingredients
* Match against keyword dictionary
* Add tags based on match threshold (editable by user)

### Google Drive Integration

* OAuth2 (installed app flow) with limited scope (drive.file)
* Initial token generation will be done via a one-off terminal script during deployment. This script fetches the OAuth token and a Refresh Token, allowing the backend to automatically renew access when it expires.
* Store tokens at /data/secrets with restricted permissions (chmod 600)
* Configure RECIPE_ROOT_FOLDER_ID

Per recipe:

* Create folder <recipe_id>/
* Upload original.jpg, thumbnail.webp, recipe.json
* Update by overwriting recipe.json

### Local Cache & Draft Storage (SQLite + FTS5)

* recipes_cache, drive_files, recipe_search, local_file_cache
* Temporary Drafts: Unsaved draft metadata is stored in SQLite. Temporary draft images are stored in a local volume at `/data/drafts` until the user hits "Save" and commits them to Google Drive.
* FTS5 over title, ingredients, steps, tags, source, raw_ocr_text
* Updated on save/sync

### File Cache (LRU)

* Directory: /data/cache
* Keyed by drive_file_id
* Evict by last_accessed_at when exceeding size limit

### Sync Job

* Interval: Every 2 hours (via FastAPI background task)
* Manual Sync: UI must include a button to trigger the sync process on demand
* Detect updated recipe.json in Drive
* Upsert cache and rebuild FTS
* Remove deleted entries

### Frontend

* Upload: file + camera + crop UI
* Draft editor: side-by-side original image + editable fields
* Search: keyword + filters
* Recipe view: MUST show original scan alongside structured data

### Deployment (Docker Compose)

```yaml
version: '3.9'
services:
  backend:
    build: ./backend
    volumes:
      - ./data:/data
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3004:3000"
```

### Security (MVP)

* LAN-only access
* OAuth tokens stored locally with restricted permissions
* No multi-user auth

### Failure Handling

* Retry Drive API calls
* Serve cached metadata/images if Drive unavailable
* Degraded mode if uncached files cannot be fetched

### Reverse Proxy (Caddy)

The application will be deployed alongside other services on a local remote server and exposed via a reverse proxy.

* A Caddy server will be used as the reverse proxy layer.
* Domain: `http://recipes.local`
* Caddy will route `/api/*` requests directly to the FastAPI backend running on port `8000`.
* Caddy will route all other requests to the React/Vite frontend service running on port `3004`.
* This ensures no CORS issues and keeps the backend ports unexposed to the outside network.

This setup allows:

* Clean local domain-based access instead of port numbers
* Centralized routing for multiple applications on the same host
* Easy coexistence with other Docker-hosted services on the server
