# ADR 005: Use Google AI LLMs for Recipe Extraction and Parsing

## Status

Accepted

## Context

The `recipe-shelf` application needs to reliably extract structured data (ingredients, instructions, metadata) and identify recipe images from raw scans and screenshots of magazine pages. These source images often feature complex, highly varied layouts. Furthermore, a single uploaded page might contain multiple distinct recipes, or a single recipe might span across multiple uploaded pages. 

Building a traditional local OCR pipeline combined with rule-based heuristics to parse such arbitrary and complex magazine layouts is technically challenging, fragile, and difficult to maintain.

## Decision

We will use Google AI LLMs (specifically Gemini) via API as the primary engine for processing scanned images and screenshots, instead of relying on a local OCR engine. 

The LLM will be responsible for:
1. Identifying recipes (handling multi-page scenarios and multiple recipes per page).
2. Extracting structured text components (title, ingredients, steps, time/servings, notes) based on schema prompts.
3. Returning bounding box coordinates for the recipe's associated picture(s).

The backend application will rely entirely on the structured JSON output provided by the LLM for parsing, and use the returned bounding boxes to crop original images locally.

## Consequences

### Positive

*   **Simplified Architecture**: Eliminates the need for complex, custom heuristic parsing logic and local OCR engine management.
*   **High Accuracy & Flexibility**: LLMs are vastly superior at understanding the semantic structure of varied magazine layouts, easily handling edge cases like multiple recipes per page or split-page recipes.
*   **Integrated Image Identification**: The LLM can identify and provide bounding boxes for relevant recipe images within the same processing step, simplifying the image extraction pipeline.

### Negative

*   **External Dependency**: Introduces a hard dependency on the Google AI API for the core parsing feature, meaning parsing cannot occur fully offline (even though the app runtime is primarily local).
*   **Latency**: The network call to the LLM API will introduce more latency compared to a purely local, lightweight extraction process.
*   **Data Processing Nuance**: To respect API limits and optimize network bandwidth, images sent to the LLM must be compressed/optimized first, while the actual cropping operation must be performed on the locally stored original high-resolution image using the coordinates returned by the API.
*   **Potential Costs**: Depending on usage volume and the specific Google AI tier, API usage may incur costs or be subject to rate limits.
