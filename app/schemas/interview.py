from pydantic import BaseModel
from typing import Optional, List

class InterviewCreate(BaseModel):
    job_title: str
    job_description: str
    category: str
    difficulty: str

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    user_answer: Optional[str] = None
    ai_feedback: Optional[str] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True

class InterviewResponse(BaseModel):
    id: int
    job_title: str
    job_description: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    overall_score: Optional[float] = None
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

class SubmitAnswer(BaseModel):
    question_id: int
    answer: str