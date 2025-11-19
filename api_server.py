from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_system import RAGSystem
import logging
import tempfile
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Knowledge Base Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_system = RAGSystem()

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    query: str
    response: str
    sources: List[dict]
    num_sources: int

class UpdateKnowledgeBaseRequest(BaseModel):
    documents_directory: str

@app.get("/")
async def root():
    return {"message": "Knowledge Base Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "knowledge-base-chatbot"}

@app.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = rag_system.ask_question(request.query, request.top_k)
        
        return QueryResponse(
            query=result["query"],
            response=result["response"],
            sources=result["sources"],
            num_sources=result["num_sources"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/stats")
async def get_knowledge_base_stats():
    try:
        stats = rag_system.get_knowledge_base_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.post("/update-knowledge-base")
async def update_knowledge_base(request: UpdateKnowledgeBaseRequest):
    try:
        if not Path(request.documents_directory).exists():
            raise HTTPException(status_code=400, detail="Documents directory does not exist")
        
        rag_system.update_knowledge_base(request.documents_directory)
        
        return {
            "status": "success", 
            "message": f"Knowledge base updated from {request.documents_directory}"
        }
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating knowledge base: {str(e)}")

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    try:
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            uploaded_files.append(file_path)
        
        rag_system.update_knowledge_base(temp_dir)
        
        # Clean up temporary files
        for file_path in uploaded_files:
            os.remove(file_path)
        os.rmdir(temp_dir)
        
        return {
            "status": "success",
            "message": f"Uploaded and processed {len(files)} documents",
            "files": [file.filename for file in files]
        }
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading documents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)