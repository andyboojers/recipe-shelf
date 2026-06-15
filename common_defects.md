# Common Defects & Resolutions

This document logs defects encountered during the development of Recipe Shelf and their resolutions.

---

## 1. Google Drive Upload: HTTP 404 Folder Not Found
- **Symptom**: Save recipe fails with `HttpError 404: File not found` when creating the subfolder inside the parent folder.
- **Root Cause**: The parent folder ID configuration (`RECIPE_ROOT_FOLDER_ID`) was set to a full Google Drive URL (e.g. `https://drive.google.com/drive/folders/...`) instead of just the clean alphanumeric ID.
- **Resolution**: Implemented `extract_folder_id` in [drive_service.py](file:///home/abooj/projects/recipe-shelf/backend/services/drive_service.py) to parse and extract the clean folder ID if a URL is provided.

---

## 2. Google Drive Upload: HTTP 403 Storage Quota Exceeded (Service Accounts)
- **Symptom**: Save recipe fails with `HttpError 403: Service Accounts do not have storage quota`.
- **Root Cause**: Google Cloud Service Accounts have 0 GB storage quota on personal Gmail drives. Any binary files uploaded by the service account count against its own quota, causing the upload to fail.
- **Resolution**: Switched to User Authentication (OAuth2) by generating a `token.json` file. Since operations are run on behalf of the user, they consume the user's personal drive quota.

---

## 3. Google Drive Upload: HTTP 403 Fallback to Service Account in Docker
- **Symptom**: Even after generating `token.json` and deploying, the application continues to throw the `403 storageQuotaExceeded` error.
- **Root Cause**: The docker deployment writes the token to `/secrets/token.json`, but `drive_service.py` was hardcoded to look for it in `/data/secrets/token.json`. Since the token wasn't found at that path, it silently fell back to the service account credentials (`/secrets/service_account.json`).
- **Resolution**: Updated `CREDENTIALS_FILE` path in [drive_service.py](file:///home/abooj/projects/recipe-shelf/backend/services/drive_service.py) to dynamically locate `token.json` relative to the configured `SERVICE_ACCOUNT_FILE` path (e.g., in `/secrets/`).
