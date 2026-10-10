from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal
from app.models import Document, DocumentStatus


from app.services import email_intake


app = FastAPI(title="DocuMind AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.router import api_router

app.include_router(api_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def recover_interrupted_jobs():
    db = SessionLocal()
    try:
        stuck = db.query(Document).filter(Document.status.in_([
            DocumentStatus.QUEUED, DocumentStatus.OCR, DocumentStatus.EXTRACTION, DocumentStatus.VALIDATION,
        ])).all()
        for doc in stuck:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Traitement interrompu, veuillez le relancer"
        db.commit()
    finally:
        db.close()



@app.on_event("startup")
def start_email_intake():
    email_intake.start()


@app.on_event("shutdown")
def stop_email_intake():
    email_intake.stop()        