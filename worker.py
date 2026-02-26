import os
from dotenv import load_dotenv
load_dotenv()
from celery import Celery
from crewai import Crew, Process
from agents import get_verifier, get_financial_analyst, get_investment_advisor, get_risk_assessor
from task import get_verification_task, get_analyze_document_task, get_investment_analysis_task, get_risk_assessment_task
from database import SessionLocal
from models import AnalysisJob

# Configure Celery
# Assumes Redis is running on localhost default port 6379
celery_app = Celery(
    "financial_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True, name="process_document_task")
def process_document_task(self, job_id: int):
    db = SessionLocal()
    try:
        # 1. Fetch Job from Database
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return f"Job {job_id} not found"

        # 2. Update status to PROCESSING
        job.status = "PROCESSING"
        db.commit()

        # 3. Instantiate Fresh Agents per request to prevent cross-contamination of memory buffers
        verifier = get_verifier()
        fin_analyst = get_financial_analyst()
        inv_advisor = get_investment_advisor()
        risk_assessor = get_risk_assessor()

        t_verify = get_verification_task(verifier)
        t_analyze = get_analyze_document_task(fin_analyst)
        t_invest = get_investment_analysis_task(inv_advisor)
        t_risk = get_risk_assessment_task(risk_assessor)

        # 4. Create Crew and run
        financial_crew = Crew(
            agents=[verifier, fin_analyst, inv_advisor, risk_assessor],
            tasks=[t_verify, t_analyze, t_invest, t_risk],
            process=Process.sequential,
        )

        print(f"Starting CrewAI for Job ID: {job_id}, Query: {job.query}, File: {job.file_path}")
        result = financial_crew.kickoff(inputs={'query': job.query, 'file_path': job.file_path})


        # 4. Save results to DB
        result_str = str(result)
        job.status = "COMPLETED"
        job.result_text = result_str
        db.commit()

        # 5. Generate slick PDF report
        try:
            from markdown_pdf import MarkdownPdf, Section
            os.makedirs("outputs", exist_ok=True)
            pdf_path = f"outputs/job_{job.id}_analysis.pdf"
            pdf = MarkdownPdf(toc_level=2)
            pdf.add_section(Section(result_str))
            pdf.save(pdf_path)
            print(f"Successfully generated PDF: {pdf_path}")
        except Exception as pdf_e:
            print(f"PDF generation failed: {pdf_e}")

        return {"job_id": job.id, "status": "COMPLETED"}

    except Exception as e:
        # Handle failures gracefully by updating the DB row
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.result_text = f"Error: {str(e)}"
            db.commit()
        print(f"Celery Task Failed: {str(e)}")
        raise e
    finally:
        db.close()
