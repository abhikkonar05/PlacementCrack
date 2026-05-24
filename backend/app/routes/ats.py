from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, ATSCheckResult
from app.database import get_db
from app.models import ATSCheck, User
from app.ai.ats_evaluator import extract_text_from_pdf, evaluate_resume

router = APIRouter(prefix="/ats", tags=["ATS Resume Checker"])


@router.post("/check", response_model=ATSCheckResult)
async def check_resume(
    role: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parses PDF resume, evaluates ATS compatibility score for target role, and saves feedback in PostgreSQL."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF file format is supported"
        )
        
    try:
        file_bytes = await file.read()
        
        # Extract text from pdf
        resume_text = extract_text_from_pdf(file_bytes)
        if not resume_text or len(resume_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from the PDF. Ensure it is a text-based PDF and not scanned."
            )
            
        # Run ATS evaluator
        eval_result = evaluate_resume(resume_text, role)
        
        # Save check in database
        check_doc = ATSCheck(
            user_id=current_user.id,
            role=role,
            score=eval_result["score"],
            matched_keywords=eval_result["matched_keywords"],
            missing_keywords=eval_result["missing_keywords"],
            suggestions=eval_result["suggestions"],
            date=datetime.now(timezone.utc)
        )
        db.add(check_doc)
        await db.flush() # Populate check_doc.id
        
        # Increment profile score by score / 10
        score_gain = round(eval_result["score"] / 10.0, 1)
        
        user_stmt = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_stmt)
        db_user = user_result.scalar_one_or_none()
        
        if db_user:
            db_user.profile_score = (db_user.profile_score or 0.0) + score_gain
            db.add(db_user)
            
        await db.commit()
        
        return ATSCheckResult(
            id=str(check_doc.id),
            user_id=str(current_user.id),
            score=eval_result["score"],
            matched_keywords=eval_result["matched_keywords"],
            missing_keywords=eval_result["missing_keywords"],
            suggestions=eval_result["suggestions"],
            date=check_doc.date
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume processing: {str(e)}"
        )


@router.get("/history", response_model=List[ATSCheckResult])
async def get_ats_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve ATS resume check history for the logged-in user from PostgreSQL."""
    try:
        stmt = select(ATSCheck).where(ATSCheck.user_id == current_user.id).order_by(desc(ATSCheck.date))
        result = await db.execute(stmt)
        history_records = result.scalars().all()
        
        return [
            ATSCheckResult(
                id=str(doc.id),
                user_id=str(doc.user_id),
                score=doc.score,
                matched_keywords=doc.matched_keywords or [],
                missing_keywords=doc.missing_keywords or [],
                suggestions=doc.suggestions or [],
                date=doc.date
            )
            for doc in history_records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ATS history: {str(e)}"
        )
