from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import get_user_by_email
from app.services.ai_service import analyze_resume
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM
import pdfplumber
import io

router = APIRouter(prefix="/resume", tags=["Resume"])
security = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db)
):
    from app.models.user import User
    from app.services.auth_service import hash_password
    user = db.query(User).filter(User.email == "default@example.com").first()
    if not user:
        user = User(
            full_name="Default User",
            email="default@example.com",
            hashed_password=hash_password("DefaultPassword123!")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.post("/analyze")
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    current_user = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        file_bytes = await file.read()
        resume_text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    resume_text += page_text + "\n"
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Failed to extract text from the PDF. The document might be empty or scanned images.")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF file: {str(e)}")

    try:
        result = analyze_resume(resume_text, job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Resume analysis failed: {str(e)}")
