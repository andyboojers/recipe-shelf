# PRD "Must Have" Implementation Status

I have cross-referenced the current state of the frontend UI, backend API, database schemas, and Gemini integration against the "Must Have" section of your PRD. Here is where we stand:

## ✅ Fully Implemented
*   **Mobile Screenshots & Scans Upload**: Fully supported via the React `ImageUploader` component.
*   **OCR Text Extraction**: Successfully utilizing Google Gemini for structured data extraction.
*   **Multiple Distinct Recipes per Page**: Gemini successfully returns an array of distinct recipes, and the `RecipeSelector` UI component correctly allows the user to choose which one to save.
*   **Structured Records**: Recipes are successfully parsed into title, ingredients, instructions, and notes.
*   **Personal Notes**: Supported in the Draft Editor and saved to the database.
*   **Local Network Accessibility**: Containerized and exposed via Vite proxy, fully accessible over the local network.

## 🚧 Partially Implemented / Needs Work
*   **Display Original Scan alongside Extracted Data**: The UI `DraftEditor` has the layout for this, but the backend is currently returning a hardcoded dummy image (mocked).
*   **Extract Relevant Recipe Images**: We instruct Gemini to return an `image_bounding_box`, but the backend does not yet use this data to actually crop the original image. It currently hardcodes an empty image path for the draft.
*   **Keyword Search**: The backend has the `/api/recipes?q=` endpoint wired up to the frontend search bar, but we still need to verify the SQLite FTS5 implementation covers all required text fields.
*   **Google Drive Storage**: The text payload saves to Drive, but image uploading and retrieval from Drive is mocked.

## ❌ Not Yet Implemented (Gaps in Must Have)
*   **Missing Schema Fields**: The PRD explicitly requires identifying `servings` and `cooking time`. These fields are currently missing from the Gemini prompt, the Pydantic schemas, and the UI.
*   **Automatic Tag Suggestion**: The PRD requires the system to "automatically suggest tags from recipe text." Gemini is not currently instructed to generate tags, and the `tags` array is missing from the database schema.

---

## What is Next?

Based on the gaps above, I recommend prioritizing the following sequence of features to complete the MVP:

1.  **Schema Completion (The Foundation):** Update the `schemas.py`, the Gemini system prompt, and the `DraftEditor` UI to include `servings`, `cooking time`, and `tags`. 
2.  **Image Processing Pipeline:** Implement the backend logic to read the uploaded base64 image, crop it using the `image_bounding_box` coordinates returned by Gemini, and save the resulting thumbnail to the draft.
3.  **Google Drive Finalization:** Remove the mock endpoints and finalize the uploading and retrieval of the cropped recipe images from Google Drive.
