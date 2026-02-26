from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import os
import uuid
import asyncio
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import AnalysisJob
from worker import process_document_task

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Document Analyzer API", version="2.0")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API with Celery Async Queue is running"}

@app.post("/analyze")
async def analyze_financial_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db)
):
    """
    Upload a financial document and enqueue it for background AI analysis.
    Returns tracking ID immediately for async polling.
    """
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        os.makedirs("data", exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        if query=="" or query is None:
            query = "Analyze this financial document for investment insights"
            
        # 1. Create a Pending Job Record in SQLite
        new_job = AnalysisJob(
            status="PENDING",
            query=query.strip(),
            file_path=file_path
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # 2. Dispatch the background Celery Task
        process_document_task.delay(new_job.id)
        
        return {
            "status": "success",
            "message": "Analysis job added to the queue.",
            "job_id": new_job.id,
            "query": query,
            "file_processed": file.filename
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error initializing job: {str(e)}")

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Poll for background analysis progression"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job.id,
        "status": job.status,
        "query": job.query,
    }
    
    if job.status in ["COMPLETED", "FAILED"]:
        if job.status == "COMPLETED":
            response["message"] = "Analysis is ready! Download your PDF report."
            response["download_url"] = f"http://localhost:8000/jobs/{job.id}/pdf"
        else:
            response["error"] = job.result_text
        
        # Cleanup PDF file once terminal state is reached
        if os.path.exists(job.file_path):
            try:
                os.remove(job.file_path)
            except:
                pass
        
    return response

@app.get("/jobs/{job_id}/pdf")
async def download_job_pdf(job_id: int):
    """Download the finalized financial analysis as a PDF"""
    from fastapi.responses import FileResponse
    pdf_path = f"outputs/job_{job_id}_analysis.pdf"
    
    if os.path.exists(pdf_path):
        return FileResponse(
            path=pdf_path, 
            filename=f"Financial_Analysis_Job_{job_id}.pdf", 
            media_type='application/pdf'
        )
    raise HTTPException(status_code=404, detail="PDF not found or still generating.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)