# Quiz Or Sheet v2 - Project Context

## 🚀 Vision
A premium AI-powered academic assistant for medical students (Al-Azhar University). It processes educational materials and generates interactive quizzes.

## 🛠 Tech Stack
- **Frontend:** Next.js 14+ (App Router), Vanilla CSS (Premium Design), Server-Sent Events for log streaming.
- **Backend:** Python FastAPI, Google Generative AI SDK (Gemini 3.1 Pro & Flash-Lite).
- **Architecture:** Decoupled Monorepo. `/frontend` and `/backend`.

## 🤖 Agentic Workflow
1. **Analyzer Agent:** Maps document structure, identifies Q&A, and plans chunking.
2. **Extractor Agents:** Sequential processing of document chunks into structured JSON (max 50 questions/chunk).
3. **Orchestrator:** Manages state and streams logs to the frontend via SSE.

## 📁 Project Structure
- `/backend`: FastAPI service.
  - `main.py`: API endpoints and SSE logic.
  - `agents.py`: Agent logic using Gemini.
- `/frontend`: Next.js application.
  - `app/page.tsx`: Main UI and orchestration.
  - `components/`: Premium UI components.
  - `lib/quizGenerator.ts`: Standalone HTML generator.

## 📜 Rules & Conventions
- **Backend:** Python is mandatory. Use professional logging (JSON).
- **Frontend:** Next.js expert patterns. No Tailwind (Vanilla CSS).
- **Deployment:** Backend must be container-ready for Cloud Run.
- **Git:** Commit after milestones. Maintain `.gitignore`.

## 📝 Change Log

### [2026-04-23] - Backend Deployment & Frontend Integration
- **Infrastructure**: Deployed the FastAPI backend to Google Cloud Run (Project: `aligna-485822`).
  - **Service URL**: `https://quiz-backend-776350978260.us-central1.run.app`
  - **Config**: Configured Dockerfile for production readiness and set up public access for the `/process` endpoint.
- **Frontend**: Updated `app/page.tsx` to utilize the live Cloud Run API instead of the local dev server.
- **Verification**: Confirmed backend health via `/health` endpoint and verified frontend UI stability via browser testing.
- **Fixes**: Resolved project billing issues by switching deployment target to an active billing-enabled project.

### [2026-04-23] - Model Upgrade to Gemini 3.1
- **Upgrade**: Switched Analyzer Agent to `gemini-3.1-flash-lite-preview` for faster, cost-effective initial mapping.
- **Upgrade**: Switched Extractor Agents to `gemini-3.1-pro-preview` for high-accuracy reasoning during question extraction.
- **Infrastructure**: Re-deployed to Cloud Run to apply model changes.

### [2026-04-23] - Quota Optimization & Sequential Processing
- **Logic**: Switched from parallel (`asyncio.gather`) to sequential extraction in `main.py` to stay within Gemini Free Tier limits.
- **Resilience**: Enhanced `tenacity` retry logic in `agents.py` (Multiplier: 10x, Max Wait: 300s, Attempts: 10) to gracefully handle heavy traffic.
- **Buffer**: Added a 5-second `asyncio.sleep` cooldown between sequential agent chunks.

### [2026-04-23] - Logging, Hydration & Stream Stability
- **Backend**: Enabled `PYTHONUNBUFFERED=1` in `Dockerfile` to ensure logs stream immediately to Cloud Run.
- **Backend**: Added internal debug tracing to the streaming generator in `main.py` for better visibility.
- **Frontend**: Fixed React hydration mismatches in `AgentTerminal` using `mounted` state checks.
- **Frontend**: Refactored SSE parser to use robust regex-based splitting (`/\n\n|\r\n\r\n/`) to prevent hangs during data streaming.
- **Deployment**: Final re-deployment to Cloud Run confirmed and healthy.

### [2026-04-23] - Quota Resilience & Sequential Extraction Tuning
- **Backend**: Reduced chunk size from 50 to **20 questions** per agent to stay within Gemini Free Tier limits.
- **Backend**: Increased cooldown between sequential chunks from 5s to **10s** in `main.py`.
- **Backend**: Implemented `retry_logger` in `agents.py` with `tenacity` to provide detailed backoff visibility in Cloud Run logs.
- **Backend**: Optimized retry strategy (Multiplier: 10x, Max Wait: 300s, Attempts: 10) specifically for `ResourceExhausted` errors.
- **Frontend**: SSE parser regex-based splitting implemented to handle inconsistent stream termination.

### [2026-04-23] - Vercel Readiness & Final Quota Hardening
- **Frontend**: Switched backend URL to dynamic environment variable `NEXT_PUBLIC_API_URL`.
- **Frontend**: Created `.env.local.example` with the Cloud Run production URL for seamless Vercel deployment.
- **GitHub**: Initialized public repository `sohailcollege2032008-tech/Quiz-Or-Sheet` and pushed the production-ready monorepo.
- **Backend**: Further reduced extraction chunk size to **10 questions** per agent to virtually eliminate `ResourceExhausted` failures.
- **Backend**: Confirmed 30-minute timeout on Cloud Run to support large document processing sessions.

### [2026-04-23] - Paid Tier Optimization & Balanced Chunking
- **Backend**: Increased chunk size limit to **50 questions** per agent as per Paid Tier capabilities.
- **Backend**: Implemented **Balanced Splitting** logic (e.g., 80 Qs -> 40/40, 90 Qs -> 50/40) for optimal reasoning.
- **Backend**: Removed 10s quota cooldown; reduced to 2s minimal buffer for SSE stability.
- **Frontend**: Created production `.env` file with `NEXT_PUBLIC_API_URL` pointing to Cloud Run.

## IMPORTANT POINT 
- IF YOU MADE ANY CHANGE IN LOGIC OR IN ANY THING IN THE PROJECT YOU SHOULD UPDATE THE GEMINI.MD OF THE PROJECT TO MAKE IT UP TO DATE 
AND MAKE A PART OF IT TO LIST THE CHANGES LIKE A COMMIT LOG BUT WITH MORE DETAILS ABOUT EVERY COMMIT