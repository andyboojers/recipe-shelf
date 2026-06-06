# Recipe Shelf - E2E & Quality Assurance Strategy

## 1. Overview
This document outlines the comprehensive testing strategy for the Recipe Shelf application to maximize the quality of production deployments. It defines the types of testing required, the strategy for regression testing, and clear responsibilities between the Lead Automated Engineer (AI) and the Product Owner (User).

## 2. Why Automated Browser UI Testing is Limited Here
While automated browser plugins are excellent for testing traditional web applications, they are explicitly not used for Recipe Shelf's primary End-to-End (E2E) testing for the following reasons:
1. **Device-Specific Workflows**: The core value proposition of Recipe Shelf involves taking physical photos of cookbooks using mobile devices (like your iPad or iPhone). Automated browser plugins running in a headless desktop environment cannot accurately simulate native mobile camera uploads, touch interactions, or responsive mobile viewports.
2. **Local Network Isolation**: The production environment (`recipes.local`) is hosted on a secure local HP server. This prevents headless automated browser containers from easily accessing and testing the true production environment without complex local network proxying.

## 3. Testing Tiers & Responsibilities

To ensure maximum quality, we split testing into multiple tiers:

### Tier 1: Unit & Integration Testing
*Focus: Code-level correctness, API contracts, and internal logic.*
- **Scope**: Backend API routes (FastAPI), database operations, Gemini extraction logic, and Google Drive API integration.
- **Responsibility**: **Lead Engineer (AI)**
- **Methodology**: Automated test scripts (`pytest`) run during development and CI/CD pipelines. We use mocking for external services (Gemini, Google Drive) where appropriate to ensure fast, deterministic tests.

### Tier 2: Automated E2E API Testing (Regression)
*Focus: Ensuring core workflows function end-to-end at the API level.*
- **Scope**: Simulating a full recipe workflow programmatically: uploading a sample image -> extracting data -> saving draft -> saving to Google Drive -> searching for the recipe.
- **Responsibility**: **Lead Engineer (AI)**
- **Methodology**: Automated API test suites that run against a staging or test database. This acts as our primary **Regression Testing** layer to ensure new code changes do not break existing core functionality.

### Tier 3: Manual E2E UI Testing
*Focus: User experience, visual layout, and real-world environmental factors.*
- **Scope**: Interacting with the React frontend, verifying layout on different screen sizes (desktop, iPad), checking UI feedback (loading states, error messages), and ensuring intuitive workflows.
- **Responsibility**: **Product Owner (User)**
- **Methodology**: Ad-hoc and pre-release testing using real browsers on actual devices.

### Tier 4: Production Verification (Smoke Testing)
*Focus: Sanity checking the live production deployment.*
- **Scope**: Uploading a real photo from a mobile device on the production server (`http://recipes.local`), verifying it extracts via Gemini, and confirming the JSON and Image appear in the correct Google Drive folder.
- **Responsibility**: **Product Owner (User)**
- **Methodology**: Manual smoke test immediately following a production deployment or infrastructure change (e.g., Nginx configuration updates).

## 4. Regression Testing Strategy
To prevent regressions (old bugs resurfacing) and maximize production stability:
1. **Automated CI/CD Checks**: Every Pull Request (feature branch) will run the automated Unit and API Integration tests. Code cannot be merged until tests pass.
2. **Defect-Driven Tests**: Whenever a bug is found in production (such as the recent Nginx `413 Payload Too Large` issue), a corresponding automated test or configuration validation check must be added to the suite to ensure it is never broken again.
3. **API Contract Verification**: Automated tests will constantly verify the structure of the data flowing between the React Frontend and the FastAPI backend.
