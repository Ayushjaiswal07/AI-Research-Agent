from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from src.agents.researcher import AIResearchAgent
from src.rag.vector_store import VectorStoreManager
import logging
import io
import hashlib
from pypdf import PdfReader
from src.rag.chunker import split_text

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize once, reused across all requests
agent = AIResearchAgent()
vector_store = VectorStoreManager()


class ResearchRequest(BaseModel):
    topic: str

class ResearchResponse(BaseModel):
    report: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_file"
    content_type = file.content_type or ""

    allowed_types = ["application/pdf", "text/plain"]
    allowed_extensions = [".pdf", ".txt"]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type not in allowed_types and ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Only PDF and plain-text files are accepted."
        )

    logger.info(f"Received upload: {filename} ({content_type})")

    try:
        raw_bytes = await file.read()

        if content_type == "application/pdf" or ext == ".pdf":
            reader = PdfReader(io.BytesIO(raw_bytes))
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        else:
            text = raw_bytes.decode("utf-8", errors="replace").strip()

        if not text:
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the uploaded file. The file may be empty or image-only."
            )

        chunks = split_text(text)
        if not chunks:
            raise HTTPException(status_code=422, detail="Text extraction produced no usable chunks.")

        file_hash = hashlib.md5(raw_bytes).hexdigest()[:8]
        metadata = {
            "url": f"uploaded://{filename}",
            "url_hash": file_hash,
            "title": filename,
            "source_type": "upload",
        }
        vector_store.add_documents(chunks, metadata)

        logger.info(f"Indexed {len(chunks)} chunks from '{filename}' into vector store.")
        return UploadResponse(
            message=f"Successfully indexed '{filename}' into the knowledge base.",
            filename=filename,
            chunks_indexed=len(chunks),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@router.post("/research", response_model=ResearchResponse)
async def generate_research(request: ResearchRequest):
    logger.info(f"Received research request for topic: {request.topic}")
    try:
        report = agent.run_research(request.topic)
        return ResearchResponse(report=report)
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))