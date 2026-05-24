from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.router import get_current_user
from app.schemas import UserResponse
from app.models import AptitudeSession, User
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/aptitude", tags=["Aptitude Test"])

class AptitudeSubmitRequest(BaseModel):
    track: str  # "Quantitative", "Logical", "Verbal"
    total_questions: int
    correct_answers: int
    score: float  # Percentage score (0 - 100)
    feedback: Optional[str] = None

@router.post("/submit")
async def submit_aptitude_test(
    payload: AptitudeSubmitRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits the score of an attempted aptitude test, saves it, and increments readiness score."""
    try:
        session = AptitudeSession(
            user_id=current_user.id,
            track=payload.track,
            total_questions=payload.total_questions,
            correct_answers=payload.correct_answers,
            score=payload.score,
            feedback=payload.feedback,
            date=datetime.now(timezone.utc)
        )
        db.add(session)
        
        # Calculate readiness score gain (e.g. 10% of percentage score)
        score_gain = round(payload.score / 10.0, 1)
        
        # Update user profile score
        user_query = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_query)
        db_user = user_result.scalar_one_or_none()
        if db_user:
            db_user.profile_score = (db_user.profile_score or 0.0) + score_gain
            db.add(db_user)
            
        await db.commit()
        return {
            "success": True,
            "message": "Aptitude test result saved successfully.",
            "score_gain": score_gain
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving aptitude test: {str(e)}"
        )

@router.get("/history")
async def get_aptitude_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches user's previous aptitude test attempts."""
    try:
        query = select(AptitudeSession).where(AptitudeSession.user_id == current_user.id).order_by(AptitudeSession.date.desc())
        result = await db.execute(query)
        sessions = result.scalars().all()
        return [
            {
                "id": str(s.id),
                "track": s.track,
                "total_questions": s.total_questions,
                "correct_answers": s.correct_answers,
                "score": s.score,
                "feedback": s.feedback,
                "date": s.date
            }
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching aptitude history: {str(e)}"
        )
