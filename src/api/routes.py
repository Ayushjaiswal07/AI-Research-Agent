from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.agents.researcher import AIResearchAgent
from src.rag.vector_store import VectorStoreManager
from src.memory.chat_memory import load_history, clear_history
import logging
import io
import json
import asyncio
import hashlib
from pypdf import PdfReader
from src.rag.chunker import split_text
from typing import List, Optional, Literal

logger = logging.getLogger(__name__)
router = APIRouter()

agent        = AIResearchAgent()
vector_store = VectorStoreManager()


# ── Models ────────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str
    selected_file_hashes: Optional[List[str]] = None
    source_mode: Literal['auto', 'web', 'file', 'both'] = 'auto'

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int
    url_hash: str

class FileInfo(BaseModel):
    filename: str
    url_hash: str
    chunk_count: int

class DeleteResponse(BaseModel):
    message: str
    chunks_deleted: int


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename     = file.filename or "uploaded_file"
    content_type = file.content_type or ""
    allowed_types      = ["application/pdf", "text/plain"]
    allowed_extensions = [".pdf", ".txt"]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type not in allowed_types and ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{content_type}'.")

    try:
        raw_bytes = await file.read()
        if content_type == "application/pdf" or ext == ".pdf":
            reader = PdfReader(io.BytesIO(raw_bytes))
            text   = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        else:
            text = raw_bytes.decode("utf-8", errors="replace").strip()

        if not text:
            raise HTTPException(status_code=422, detail="Could not extract text from the file.")

        chunks = split_text(text)
        if not chunks:
            raise HTTPException(status_code=422, detail="No usable chunks from file.")

        file_hash = hashlib.md5(raw_bytes).hexdigest()[:8]
        vector_store.add_documents(chunks, {
            "url": f"uploaded://{filename}",
            "url_hash": file_hash,
            "title": filename,
            "source_type": "upload",
        })
        return UploadResponse(
            message=f"Successfully indexed '{filename}'.",
            filename=filename,
            chunks_indexed=len(chunks),
            url_hash=file_hash,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


# ── Files ─────────────────────────────────────────────────────────────────────

@router.get("/files", response_model=List[FileInfo])
async def list_files():
    try:
        return vector_store.list_uploaded_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{url_hash}", response_model=DeleteResponse)
async def delete_file(url_hash: str):
    try:
        deleted = vector_store.delete_uploaded_file(url_hash)
        if deleted == 0:
            raise HTTPException(status_code=404, detail=f"No file found with hash '{url_hash}'.")
        return DeleteResponse(message=f"Deleted file (hash: {url_hash}).", chunks_deleted=deleted)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
async def get_history():
    try:
        return load_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def delete_history():
    try:
        clear_history()
        return {"message": "Chat history cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Research (SSE) ────────────────────────────────────────────────────────────

@router.post("/research")
async def generate_research(request: ResearchRequest):
    async def event_stream():
        loop  = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def on_step(text: str):
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "step", "text": text})

        def run():
            try:
                report = agent.run_research(
                    request.topic,
                    selected_file_hashes=request.selected_file_hashes or [],
                    source_mode=request.source_mode,
                    on_step=on_step,
                )
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "report", "text": report})
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "text": str(e)})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        import threading
        threading.Thread(target=run, daemon=True).start()

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
