# Quiz Or Sheet v2 - Project Context

## 🚀 Vision
A premium AI-powered academic assistant for medical students (Al-Azhar University). It processes educational materials and generates interactive quizzes.

## 🛠 Tech Stack
- **Frontend:** Next.js 14+ (App Router), Vanilla CSS (Premium Design), Server-Sent Events for log streaming.
- **Backend:** Python FastAPI, Google Generative AI SDK (Gemini 2.5 Flash).
- **Architecture:** Decoupled Monorepo. `/frontend` and `/backend`.

## 🤖 Agentic Workflow
1. **Analyzer Agent:** Maps document structure, identifies Q&A, and plans chunking.
2. **Extractor Agents:** Parallel processing of document chunks into structured JSON.
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
