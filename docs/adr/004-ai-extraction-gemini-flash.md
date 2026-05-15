# ADR 004: Use Google Gemini Flash for OCR and Extraction

## Context
The core value proposition of the Recipe Shelf application is the ability to upload photos of magazine pages and automatically extract structured recipe data (titles, ingredients, instructions) and identify photographs of the food. Traditional OCR solutions (like Tesseract) struggle heavily with complex, multi-column magazine layouts and cannot parse semantics.

## Decision
We decided to use **Google Gemini Flash** (specifically the `gemini-flash-latest` multimodal model) to handle both the visual OCR and the semantic extraction in a single API call.

## Consequences

### Positive
*   **Multimodal Capabilities**: The model can "see" the image, read the text, understand the layout, and return structured JSON—all at once.
*   **Bounding Boxes**: Gemini possesses the spatial awareness to return relative bounding box coordinates (`ymin`, `xmin`, `ymax`, `xmax`) for food photos, enabling our backend to auto-crop images.
*   **Speed and Cost**: The Flash model is incredibly fast and offers generous free-tier limits, making it perfect for rapid prototyping and MVP development.

### Negative
*   **Vendor Lock-in**: The application is entirely dependent on Google's specific Generative AI API structure.
*   **Non-Determinism**: As a Generative AI model, extraction accuracy can occasionally vary or hallucinate, requiring robust fallback handling and human-in-the-loop editing workflows.
