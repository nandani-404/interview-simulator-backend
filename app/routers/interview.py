from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.schemas.interview import InterviewCreate, InterviewResponse, SubmitAnswer
from app.models.interview import Interview, Question
from app.services.ai_service import generate_questions, evaluate_answer
from app.services.auth_service import get_user_by_email
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/interview", tags=["Interview"])
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

@router.post("/start", response_model=InterviewResponse)
def start_interview(
    data: InterviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        questions = generate_questions(data.job_title, data.job_description, data.category, data.difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI question generation failed: {str(e)}")

    interview = Interview(
        user_id=current_user.id,
        job_title=data.job_title,
        job_description=data.job_description,
        category=data.category,
        difficulty=data.difficulty
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    for q_text in questions:
        question = Question(
            interview_id=interview.id,
            question_text=q_text
        )
        db.add(question)

    db.commit()
    db.refresh(interview)
    return interview

@router.post("/answer")
def submit_answer(
    data: SubmitAnswer,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    interview = db.query(Interview).filter(Interview.id == question.interview_id).first()
    try:
        result = evaluate_answer(question.question_text, data.answer, interview.job_title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI answer evaluation failed: {str(e)}")
    
    question.user_answer = data.answer
    question.ai_feedback = result.get("feedback")
    question.score = result.get("score")
    db.commit()
    
    all_questions = db.query(Question).filter(
        Question.interview_id == interview.id,
        Question.score != None
    ).all()
    
    if len(all_questions) > 0:
        avg_score = sum(q.score for q in all_questions) / len(all_questions)
        interview.overall_score = avg_score
        db.commit()
    
    return {
        "score": result.get("score"),
        "feedback": result.get("feedback"),
        "strengths": result.get("strengths"),
        "improvements": result.get("improvements"),
        "tip": result.get("tip"),
        "sample_answer": result.get("sample_answer")
    }

@router.get("/my-interviews")
def get_my_interviews(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    interviews = db.query(Interview).filter(
        Interview.user_id == current_user.id
    ).all()
    return interviews


@router.get("/stats")
def get_interview_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get total interviews
    total_interviews = db.query(Interview).filter(
        Interview.user_id == current_user.id
    ).count()

    # Get completed interviews (where overall_score is not None)
    completed_interviews = db.query(Interview).filter(
        Interview.user_id == current_user.id,
        Interview.overall_score != None
    ).all()

    # Calculate stats
    if not completed_interviews:
        return {
            "total_interviews": total_interviews,
            "average_score": 0,
            "best_score": 0,
            "most_practiced_category": "N/A",
            "scores_over_time": [],
            "category_breakdown": {}
        }

    scores = [i.overall_score for i in completed_interviews]
    avg_score = sum(scores) / len(scores)
    best_score = max(scores)

    # Line chart: score trend over last 10 completed interviews
    # Sorted chronologically (older to newer) for the chart
    last_10 = db.query(Interview).filter(
        Interview.user_id == current_user.id,
        Interview.overall_score != None
    ).order_by(Interview.created_at.desc()).limit(10).all()
    
    # Reverse to make it chronological (left to right)
    last_10.reverse()
    
    scores_over_time = [
        {
            "id": i.id,
            "job_title": i.job_title,
            "score": round(i.overall_score, 1),
            "date": i.created_at.strftime("%Y-%m-%d") if i.created_at else "N/A"
        }
        for i in last_10
    ]

    # Bar chart: average score by category
    category_data = db.query(
        Interview.category,
        func.avg(Interview.overall_score).label("avg_score"),
        func.count(Interview.id).label("count")
    ).filter(
        Interview.user_id == current_user.id,
        Interview.overall_score != None
    ).group_by(Interview.category).all()

    category_breakdown = {
        row.category if row.category else "General": round(row.avg_score, 1)
        for row in category_data
    }

    # Find most practiced category
    most_practiced = "N/A"
    max_count = 0
    for row in category_data:
        if row.category and row.count > max_count:
            max_count = row.count
            most_practiced = row.category

    return {
        "total_interviews": total_interviews,
        "average_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "most_practiced_category": most_practiced,
        "scores_over_time": scores_over_time,
        "category_breakdown": category_breakdown
    }