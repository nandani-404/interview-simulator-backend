from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import user, interview
from app.routers import auth, interview as interview_router, resume

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Interview Simulator",
    description="Practice interviews with AI feedback",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(interview_router.router)
app.include_router(resume.router)

@app.get("/")
def home():
    return {"message": "AI Interview Simulator API is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}