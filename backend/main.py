import os
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from agents import QuizAgents
from sse_starlette.sse import EventSourceResponse

load_dotenv()

app = FastAPI(title="Quiz Or Sheet v2 API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
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
    mime_type = file.content_type
    
    async def event_generator():
        try:
            yield {"event": "log", "data": f"Phase 1: Dispatching Analyzer Agent to map {file.filename}..."}
            plan = await agents.analyze_document(file_content, mime_type)
            
            if not plan.hasAnswers:
                yield {"event": "error", "data": "Analyzer Report: No clear questions found."}
                return

            yield {"event": "log", "data": f"Analyzer Report: Found {plan.totalQuestions} questions. Splitting into {len(plan.chunks)} chunks."}
            
            all_questions = []
            
            # Phase 2: Parallel Extraction
            yield {"event": "log", "data": "Phase 2: Dispatching Extractor Agents in parallel..."}
            
            tasks = []
            for i, chunk in enumerate(plan.chunks):
                yield {"event": "log", "data": f"Agent #{i+1} assigned to Q{chunk.start} to Q{chunk.end}"}
                tasks.append(agents.extract_chunk(file_content, mime_type, chunk.start, chunk.end, i+1))
            
            results = await asyncio.gather(*tasks)
            
            for chunk_res in results:
                all_questions.extend([q.dict() for q in chunk_res])
            
            yield {"event": "log", "data": f"Phase 3: Aggregation complete. Total: {len(all_questions)} questions."}
            yield {"event": "result", "data": json.dumps(all_questions)}
            yield {"event": "done", "data": "Mission Accomplished!"}
            
        except Exception as e:
            yield {"event": "error", "data": f"FATAL ERROR: {str(e)}"}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
