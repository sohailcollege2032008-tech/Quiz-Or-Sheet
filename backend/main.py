import os
import json
import asyncio
import logging
import logging.config
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agents import QuizAgents
from sse_starlette.sse import EventSourceResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quiz Or Sheet v2 API")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/jpeg",
    "image/png",
}

_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agents = QuizAgents()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/process")
async def process_document(request: Request, file: UploadFile = File(...)):
    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}. Allowed: PDF, DOCX, TXT, JPG, PNG.",
        )

    async def event_generator():
        try:
            logger.info(f"Phase 1: Dispatching Analyzer Agent for {file.filename}")
            yield {"event": "log", "data": f"Phase 1: Dispatching Analyzer Agent to map {file.filename}..."}
            plan = await agents.analyze_document(file_content, mime_type)

            if not plan.hasAnswers:
                logger.warning("Analyzer found no answers in the document")
                yield {"event": "error", "data": "Analyzer Report: No clear questions found."}
                return

            logger.info(f"Analyzer found {plan.totalQuestions} questions in {len(plan.chunks)} chunks")
            yield {"event": "log", "data": f"Analyzer Report: Found {plan.totalQuestions} questions. Splitting into {len(plan.chunks)} chunks."}

            all_questions = []

            logger.info("Phase 2: Starting sequential extraction")
            yield {"event": "log", "data": "Phase 2: Dispatching Extractor Agents sequentially..."}

            for i, chunk in enumerate(plan.chunks):
                logger.info(f"Agent #{i+1} extracting Q{chunk.start}-Q{chunk.end}")
                yield {"event": "log", "data": f"Agent #{i+1} assigned to Q{chunk.start} to Q{chunk.end}..."}
                chunk_res = await agents.extract_chunk(file_content, mime_type, chunk.start, chunk.end, i + 1)
                all_questions.extend([q.model_dump() for q in chunk_res])

                if i < len(plan.chunks) - 1:
                    await asyncio.sleep(2)

            logger.info(f"Phase 3 complete. Total questions extracted: {len(all_questions)}")
            yield {"event": "log", "data": f"Phase 3: Aggregation complete. Total: {len(all_questions)} questions."}
            yield {"event": "result", "data": json.dumps(all_questions)}
            yield {"event": "done", "data": "Mission Accomplished!"}

        except Exception as e:
            logger.error(f"Fatal error during processing: {e}", exc_info=True)
            yield {"event": "error", "data": f"FATAL ERROR: {str(e)}"}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
