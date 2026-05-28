from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from src.agents.researcher import AIResearchAgent
import logging
import io
from pypdf import PdfReader
from src.rag.chunker import split_text


logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the agent once to be reused across requests
agent = AIResearchAgent()

class ResearchRequest(BaseModel):
    topic: str

class ResearchResponse(BaseModel):
    report: str

@router.post("/research", response_model=ResearchResponse)
async def generate_research(request: ResearchRequest):
    if request.topic.lower().strip() in ["hi", "hii", "hello", "hey"]:
        return ResearchResponse(report="Hello! I am your AI Research Assistant. Ask me a question and I will research it for you.")
    logger.info(f"Received research request for topic: {request.topic}")
    try:
        # Run the synchronous agent logic
        report = agent.run_research(request.topic)
        
        if "Task Failed" in report:
            raise HTTPException(status_code=400, detail=report)
            
        return ResearchResponse(report=report)
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
