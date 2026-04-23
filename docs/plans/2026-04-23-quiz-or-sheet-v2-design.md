# Quiz Or Sheet v2 - Design Document

## 1. Goal
Convert the Gemini Canvas HTML reference into a production-ready local application with a decoupled architecture. This setup will facilitate easy deployment to Cloud Run and provide a premium, medical-student-oriented user experience.

## 2. Architecture
- **Frontend**: Next.js 14+ (App Router, TypeScript).
- **Backend**: Python 3.10+ (FastAPI).
- **Agentic Logic**: Ported from Canvas JS to Python using the Google Generative AI SDK.
- **Containerization**: Separate Dockerfiles for Frontend and Backend.

## 3. Data Flow
1. **User Interaction**: User uploads a document (PDF, DOCX, TXT) via the Next.js UI.
2. **Backend Processing**: 
    - `POST /process`: Receives the file.
    - `Analyzer Agent`: Scans document structure and plans chunks.
    - `Extractor Agents`: Run in parallel (async) to extract Q&A JSON.
3. **Real-time Monitoring**: Logs are streamed to the frontend via SSE (Server-Sent Events) to populate the "Agent Terminal".
4. **Final Output**: Backend returns the aggregated JSON.
5. **Generation**: Frontend generates a standalone HTML quiz file (matching the reference UI) and triggers a download.

## 4. UI/UX Design
- **Theme**: Dark Mode, Glassmorphism, Academic/Medical aesthetic.
- **Main Components**:
    - `UploadZone`: Drag-and-drop with file type validation.
    - `AgentTerminal`: Real-time log streaming from the backend.
    - `PreviewModal`: Quick view of extracted questions.
    - `DownloadManager`: Generates the standalone HTML quiz.

## 5. Security & Environment
- `.env` file in the backend to store `GEMINI_API_KEY`.
- CORS configuration to allow local communication between `localhost:3000` and `localhost:8000`.

## 6. Implementation Plan (Next Steps)
- Initialize Git repository.
- Scaffold `frontend/` (Next.js) and `backend/` (FastAPI).
- Implement the Agentic logic in Python.
- Build the Premium UI.
- Verify the HTML generator matches the reference.
