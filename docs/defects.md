# Project Defects Log

This document tracks all significant defects, their root causes, and how they were resolved to prevent them from recurring.

## Defect 001: Unhandled Extraction Exceptions
**Date:** 2026-05-15

### Description
The frontend displayed an opaque "Error extracting recipes" alert to the user after they attempted to upload an image. This occurred immediately after the EXIF orientation fix was pushed, leading to confusion about whether the EXIF update broke the system.

### Root Cause Analysis
Upon inspecting the backend logs and test suite, two separate but related issues were discovered:

1. **Non-Deterministic LLM Output**: The `backend/main.py` code assumed that `gemini_result.get("recipes", [])` would *always* return a list of Python dictionaries. Because Generative AI models are non-deterministic, Gemini occasionally hallucinated and returned a list of strings instead. 
   When the code attempted to execute `recipe.get("title")` on a string, Python threw an `AttributeError`, causing a 500 Internal Server Error.
2. **Missing Error Boundaries**: The `/api/extract` endpoint did not have a global `try/except` block. Consequently, when the `AttributeError` (or any other unexpected error, like SQLite's `OperationalError: database is locked`) occurred, FastAPI threw an unhandled 500 error instead of returning a graceful JSON payload. This left the frontend with `response.ok = false` and no contextual error message.

Furthermore, it was discovered that 5 unit tests were failing because they had not been updated to match the new API schemas and function signatures introduced in the multi-step UI update.

### Resolution
1. **Type Checking**: Added an `if not isinstance(recipe, dict): continue` check before processing each recipe draft, ensuring hallucinatory strings are safely ignored.
2. **Error Boundary**: Wrapped the entire `/api/extract` endpoint in a `try/except` block that explicitly returns an `HTTPException(status_code=500, detail=str(e))` to ensure the frontend receives diagnostic information.
3. **Test Suite Update**: Updated `backend/tests/test_extraction.py` and `backend/tests/test_storage.py` to match the correct mocked responses and function signatures.

### Prevention
*   **Always Type Check LLM Output**: Never assume the structure of data returned by an LLM is correct. Use explicit type checking or Pydantic validation before accessing dictionary keys.
*   **Keep Tests Green**: Ensure the test suite is run locally before merging any feature branch, as per the `/finish` workflow.
