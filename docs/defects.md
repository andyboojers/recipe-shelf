# Project Defects Log

This document tracks all significant defects, their root causes, and how they were resolved to prevent them from recurring.

## Defect 001: Unhandled Extraction Exceptions
**Date:** 2026-05-15

### Description
The frontend displayed an opaque "Error extracting recipes" alert to the user after they attempted to upload an image. This occurred immediately after the EXIF orientation fix was pushed, leading to confusion about whether the EXIF update broke the system.

### Root Cause Analysis
Upon inspecting the backend logs and test suite, two separate but related issues were discovered:

1. **Non-Deterministic LLM Output**: The `backend/main.py` code assumed that `gemini_result.get("recipes", [])` would *always* return a list of Python dictionaries. Because Generative AI models are non-deterministic, Gemini occasionally hallucinated and returned a list of strings instead, or even `{"recipes": null}`. 
   When the code attempted to execute `recipe.get("title")` on a string, or iterate over a `NoneType` object, Python threw an exception (`AttributeError` or `TypeError`), causing a 500 Internal Server Error.
2. **Missing Error Boundaries & UI Masking**: The `/api/extract` endpoint did not have a global `try/except` block. Even worse, the frontend `ImageUploader.jsx` hardcoded `throw new Error('Extraction failed')` without actually parsing the JSON `detail` payload from the 500 error. This left the frontend with an opaque error message that masked the true root cause.

Furthermore, it was discovered that 5 unit tests were failing because they had not been updated to match the new API schemas and function signatures introduced in the multi-step UI update.

### Resolution
1. **Type Checking**: Added an `if not isinstance(recipe, dict): continue` check before processing each recipe draft, ensuring hallucinatory strings are safely ignored.
2. **Error Boundary**: Wrapped the entire `/api/extract` endpoint in a `try/except` block that explicitly returns an `HTTPException(status_code=500, detail=str(e))` to ensure the frontend receives diagnostic information.
3. **Test Suite Update**: Updated `backend/tests/test_extraction.py` and `backend/tests/test_storage.py` to match the correct mocked responses and function signatures.

### Prevention
*   **Always Type Check LLM Output**: Never assume the structure of data returned by an LLM is correct. Use explicit type checking or Pydantic validation before accessing dictionary keys.
*   **Keep Tests Green**: Ensure the test suite is run locally before merging any feature branch, as per the `/finish` workflow.

## Defect 002: Broken Draft Image Rendering
**Date:** 2026-05-16

- [x] Fix broken draft image rendering on Edit Recipe page.

### Description
On the "Edit Recipe Draft" page, the recipe image renders as a broken icon.

### Root Cause Analysis
The frontend `DraftEditor.jsx` component attempts to load the image using `/api/files/${draft.image_path}`. However, `draft.image_path` stores the full absolute server file path (e.g., `/home/abooj/...`), resulting in an invalid URL. Furthermore, there is no endpoint on the backend to serve local draft images; the `/api/files/{drive_file_id}` endpoint is mocked and does not handle local files.

### Resolution
1. **New Backend Endpoint**: Added a GET `/api/drafts/{draft_id}/image` endpoint in [backend/main.py](file:///home/abooj/projects/recipe-shelf/backend/main.py) to read and return the draft's cropped image from the local filesystem (`data/drafts/{draft_id}.jpg`).
2. **Frontend Update**: Updated [frontend/src/components/DraftEditor.jsx](file:///home/abooj/projects/recipe-shelf/frontend/src/components/DraftEditor.jsx) to target the new draft image endpoint.
3. **Unit Testing**: Added `test_get_draft_image_endpoint` in [backend/tests/test_storage.py](file:///home/abooj/projects/recipe-shelf/backend/tests/test_storage.py) which verifies image serving works correctly.

---

## Defect 003: iPhone HEIC Upload Failure
**Date:** 2026-06-21

- [x] Fix Defect 003: iPhone HEIC Upload Failure

### Description
When uploading a photo taken directly with an iPhone camera (natively in HEIC/HEIF format), the extraction process fails with an opaque "Load failed" message. The same image uploaded from Windows works because it has been converted to JPEG and contains a standard MIME type.

### Root Cause Analysis
1. **MIME Type Mapping:** In iOS/Safari, HEIC images selected from files sometimes have empty MIME types, which the frontend falls back to `application/octet-stream`. The Gemini API rejects `application/octet-stream` with a `400 Unsupported MIME type` error.
2. **Missing Backend HEIC Image Support:** If the frontend correctly passes `image/heic` or `image/heif`, the backend's Python `Pillow` library throws `PIL.UnidentifiedImageError` during cropping because Pillow does not support HEIC/HEIF natively without additional packages like `pillow-heif`.

### Resolution
1. **Frontend MIME Type Resolution**: Updated [ImageUploader.jsx](file:///home/abooj/projects/recipe-shelf/frontend/src/components/ImageUploader.jsx) to automatically infer the MIME type (`image/heic` or `image/heif`) from the filename extension if `file.type` is empty or generic, avoiding backend/Gemini API `400 Unsupported MIME type` errors.
2. **Pillow HEIC Opener Registration**: Added `pillow-heif` dependency to [requirements.txt](file:///home/abooj/projects/recipe-shelf/backend/requirements.txt) and registered the HEIF/HEIC opener via `register_heif_opener()` in [main.py](file:///home/abooj/projects/recipe-shelf/backend/main.py) on application startup. This allows Pillow to seamlessly decode and crop HEIC images.
3. **Unit Testing**: Added `test_heic_image_loading` in [test_storage.py](file:///home/abooj/projects/recipe-shelf/backend/tests/test_storage.py) which verifies native HEIC/HEIF file reading.

---

## Defect 004: CI/CD Test HEIC Path Failure
**Date:** 2026-06-21

- [x] Fix Defect 004: CI/CD Test HEIC Path Failure

### Description
In the CI/CD deployment pipeline, the backend validation step (`Install & Validate Backend`) fails during pytest execution. The errors indicate that `test.heic` is missing, even though the file is tracked in git.

### Root Cause Analysis
The unit tests reference the test image file using a hardcoded relative path: `heic_path = "backend/tests/test.heic"`. 
Locally, pytest is run from the repository root, so this path resolves correctly. However, in the CI/CD pipeline, the working directory is set to `./backend` before running pytest. This causes the test to look for `backend/backend/tests/test.heic`, resulting in a file missing error.

### Resolution
Resolved the path to `test.heic` dynamically in [test_storage.py](file:///home/abooj/projects/recipe-shelf/backend/tests/test_storage.py) and [test_extraction.py](file:///home/abooj/projects/recipe-shelf/backend/tests/test_extraction.py) relative to `__file__`:
```python
heic_path = os.path.join(os.path.dirname(__file__), "test.heic")
```
This ensures the tests run successfully regardless of whether they are executed from the repository root or from the `./backend` directory.





