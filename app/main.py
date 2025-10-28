"""Main FastAPI application."""
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.models import (
    ChatRequest, ChatResponse, HealthResponse, 
    DocumentUploadResponse
)
from app.services.agent import AssistantAgent
from app.services.rag import RAGService
from app.database.db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
agent: AssistantAgent = None
rag_service: RAGService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global agent, rag_service
    
    logger.info("Starting LLM Assistant application...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize RAG service
    rag_service = RAGService()
    await rag_service.initialize()
    logger.info("RAG service initialized")
    
    # Initialize agent
    agent = AssistantAgent(rag_service=rag_service)
    logger.info("Assistant agent initialized")
    
    yield
    
    logger.info("Shutting down LLM Assistant application...")


# Create FastAPI application
app = FastAPI(
    title="LLM Assistant API",
    description="Многофункциональный LLM-ассистент с RAG, SQL и Web Search",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "name": "LLM Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check LLM availability
        llm_available = agent is not None
        
        # Check vector store
        vector_store_available = rag_service is not None and rag_service.vector_store is not None
        
        # Check database
        database_available = True  # TODO: Add actual DB check
        
        return HealthResponse(
            status="healthy" if all([llm_available, vector_store_available, database_available]) else "degraded",
            version="1.0.0",
            llm_available=llm_available,
            vector_store_available=vector_store_available,
            database_available=database_available
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the assistant.
    
    The assistant will automatically choose the best tool (RAG, SQL, Web Search)
    based on the user's question.
    """
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Assistant not initialized")
        
        logger.info(f"Processing chat request: {request.message}")
        
        # Process the request
        response = await agent.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            use_rag=request.use_rag,
            use_sql=request.use_sql,
            use_web_search=request.use_web_search
        )
        
        logger.info(f"Chat response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload documents to the RAG knowledge base.
    
    Supports: PDF, TXT, MD files
    """
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        logger.info(f"Uploading {len(files)} documents")
        
        total_chunks = 0
        for file in files:
            content = await file.read()
            chunks = await rag_service.add_document(
                content=content.decode('utf-8'),
                filename=file.filename
            )
            total_chunks += chunks
        
        return DocumentUploadResponse(
            message="Documents uploaded successfully",
            documents_processed=len(files),
            chunks_created=total_chunks
        )
        
    except Exception as e:
        logger.error(f"Error uploading documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/clear")
async def clear_documents():
    """Clear all documents from the RAG knowledge base."""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        await rag_service.clear_documents()
        return {"message": "All documents cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )

