
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String, nullable=False)
    job_description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    difficulty = Column(String(20), nullable=True)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="interviews")
    questions = relationship("Question", back_populates="interview")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    score = Column(Float, nullable=True)

    interview = relationship("Interview", back_populates="questions")