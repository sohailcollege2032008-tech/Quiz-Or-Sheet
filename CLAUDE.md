# Quiz Or Sheet v2 — Project CLAUDE.md

> **For any AI agent reading this:** This file is the single source of truth for this project. Read it fully before touching any code.

---

## 🎯 Project Overview

An AI-powered quiz generator for medical students at Al-Azhar University. The user uploads a PDF/DOCX/image of a study sheet (MCQs with answers), and the system extracts all questions and generates a standalone interactive HTML quiz file.

Built and maintained by **Sohail Ahmed** — medical student, Data Team Lead Batch 62, vibe coder.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (App Router), Vanilla CSS, SSE client |
| Backend | Python FastAPI, `sse-starlette` |
| AI | Google Gemini API (`google-generativeai`) |
| Deployment (Backend) | Google Cloud Run |
| Deployment (Frontend) | Vercel |
| Infra tooling | gcloud CLI, GitHub |

---

## 🏗 Architecture

```
User uploads file
      │
      ▼
Frontend (Next.js) ──POST /process──► Backend (FastAPI)
                    ◄─── SSE stream ──
                          │
                     ┌────▼────┐
                     │Analyzer │  gemini-3.1-flash-lite-preview
                     │ Agent   │  Maps doc, counts Qs, plans chunks
                     └────┬────┘
                          │ AnalysisPlan JSON
                     ┌────▼────────────────┐
                     │ Extractor Agents     │  gemini-3.1-pro-preview
                     │ (sequential, ≤50 Q) │  Extract structured Q&A
                     └────┬────────────────┘
                          │ List[Question]
                     ┌────▼────┐
                     │Frontend │  generateStandaloneQuiz() → HTML
                     │downloads│  interactive quiz file
                     └─────────┘
```

### SSE Event Types (Backend → Frontend)
- `log` — progress message (shown in Agent Terminal)
- `result` — final JSON array of `{q, a[], c}` questions
- `error` — error message
- `done` — stream complete

### Question JSON Schema
```json
{"q": "Question text", "a": ["Option A", "Option B", "Option C", "Option D"], "c": 0}
```
`c` = 0-based index of the correct answer.

---

## 📁 Project Structure

```
Quiz Or Sheet v2/
├── backend/
│   ├── main.py              # FastAPI app, /health + /process endpoints, SSE orchestration
│   ├── agents.py            # QuizAgents class: Analyzer + Extractor using Gemini
│   ├── requirements.txt     # Python dependencies (no pinned versions — Pydantic v2 is default)
│   ├── Dockerfile           # Cloud Run container (python:3.10-slim, port 8080)
│   ├── .env                 # Local dev secrets (gitignored)
│   ├── test_extraction.py   # E2E test: python test_extraction.py <pdf_path>
│   └── test_cloud_run.py    # Cloud Run smoke test
├── frontend/
│   ├── app/
│   │   └── page.tsx         # Main UI: file upload + SSE log terminal
│   ├── components/
│   │   └── UploadZone.tsx   # Drag-and-drop file input component
│   ├── lib/
│   │   └── quizGenerator.ts # Generates standalone HTML quiz from questions array
│   └── .env                 # NEXT_PUBLIC_API_URL (gitignored)
├── GEMINI.md                # Changelog — MUST be updated after every code change
└── CLAUDE.md                # This file
```

---

## 🌐 Infrastructure & Deployment

### Google Cloud Run (Backend)
- **Project ID:** `aligna-485822`
- **Service name:** `quiz-backend`
- **Region:** `us-central1`
- **Service URL:** `https://quiz-backend-776350978260.us-central1.run.app`
- **Timeout:** 30 minutes (supports large document processing)
- **Access:** Public (`--allow-unauthenticated`)

**Redeploy command:**
```bash
cd backend
gcloud run deploy quiz-backend \
  --source . \
  --project aligna-485822 \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=<key>,ALLOWED_ORIGINS=<frontend_url>"
```

### GitHub
- **Repo:** `https://github.com/sohailcollege2032008-tech/Quiz-Or-Sheet`
- **Branch:** `master`

### Vercel (Frontend)
- Set `NEXT_PUBLIC_API_URL=https://quiz-backend-776350978260.us-central1.run.app` in Vercel environment variables.
- Once you have the Vercel URL, update `ALLOWED_ORIGINS` in Cloud Run to that URL (currently `*`).

---

## 🔑 Environment Variables

### Backend `.env` (local dev only)
```env
GEMINI_API_KEY=<your_gemini_api_key>
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
```

### Cloud Run Environment Variables
Set via `--set-env-vars` during `gcloud run deploy`:
- `GEMINI_API_KEY` — Google AI Studio API key
- `ALLOWED_ORIGINS` — comma-separated list of allowed frontend origins (e.g. `https://your-app.vercel.app,http://localhost:3000`)

### Frontend `.env` (local dev only)
```env
NEXT_PUBLIC_API_URL=https://quiz-backend-776350978260.us-central1.run.app
```

---

## 🤖 AI Models Used

| Agent | Model | Purpose |
|-------|-------|---------|
| Analyzer | `gemini-3.1-flash-lite-preview` | Fast doc analysis, question counting, chunk planning |
| Extractor | `gemini-3.1-pro-preview` | Accurate question extraction (structured JSON) |

**Chunking rule:** Max 50 questions per chunk. Balanced splitting (e.g. 80 Qs → 40/40).

---

## ⚠️ Critical Rules & Known Gotchas

1. **Pydantic v2 — no `parse_raw`, no `.dict()`**
   - Use `Model.model_validate_json(text)` instead of `Model.parse_raw(text)`
   - Use `instance.model_dump()` instead of `instance.dict()`

2. **Gemini SDK async calls**
   - Always use `await model.generate_content_async([...])` inside async functions.
   - Never call the sync `generate_content()` in async context — it blocks the event loop.

3. **JSON stripping**
   - Gemini often wraps JSON in ```json ... ``` markdown fences.
   - Use `_strip_markdown_json()` from `agents.py` (regex-based, handles edge cases).

4. **CORS**
   - CORS origins are set via `ALLOWED_ORIGINS` env var (comma-separated).
   - Local default: `http://localhost:3000`. Production: set to your Vercel URL.

5. **File limits**
   - Max upload size: **50 MB** (enforced server-side in `main.py`).
   - Allowed MIME types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`, `image/jpeg`, `image/png`.

6. **GEMINI.md must stay updated**
   - After every code change, add an entry to `GEMINI.md` changelog with details.

---

## 🚀 Local Development

### Start backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### Run E2E test
```bash
cd backend
python test_extraction.py "C:/path/to/your/test.pdf"
# or: TEST_PDF_PATH="C:/path/to/test.pdf" python test_extraction.py
```

---

## 📜 Conventions

- **Backend language:** Python only. No Node/JS in the backend.
- **Frontend styling:** Vanilla CSS only. No Tailwind.
- **No hardcoded secrets** — all via `.env` / Cloud Run env vars.
- **Logging:** Use Python `logging` module with JSON format. No raw `print()` in production code.
- **Git:** Commit after every milestone. Keep `.gitignore` clean.
- **After every change:** Update `GEMINI.md` changelog.
