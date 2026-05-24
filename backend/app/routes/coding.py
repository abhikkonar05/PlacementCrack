from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, CodingSubmissionCreate, CodingSubmissionResponse
from app.database import get_db
from app.models import Submission, User
from app.sandbox.code_runner import PROBLEMS, run_code_sandbox

router = APIRouter(prefix="/coding", tags=["Coding Test"])

PROBLEM_SEQUENCE = ["two_sum", "longest_substring", "trapping_rain_water"]

async def check_is_unlocked(problem_id: str, user_id: str, db: AsyncSession) -> bool:
    """Enforces database-driven progression locks based on prior passes."""
    if problem_id not in PROBLEM_SEQUENCE:
        return False
        
    idx = PROBLEM_SEQUENCE.index(problem_id)
    if idx == 0:
        return True # First problem is always unlocked
        
    # Check if user has passed the previous problem in sequence
    prev_problem_id = PROBLEM_SEQUENCE[idx - 1]
    stmt = select(Submission.id).where(
        Submission.user_id == user_id,
        Submission.problem_id == prev_problem_id,
        Submission.status == "Pass"
    ).limit(1)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


@router.get("/problems")
async def get_problems(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch DSA challenges indicating dynamic locked/unlocked states based on progression."""
    try:
        problems_list = []
        for pid, prob in PROBLEMS.items():
            unlocked = await check_is_unlocked(pid, current_user.id, db)
            problems_list.append({
                "id": pid,
                "title": prob["title"],
                "difficulty": prob["difficulty"],
                "description": prob["description"],
                "template": prob["template"],
                "unlocked": unlocked
            })
        return problems_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching problems: {str(e)}"
        )


@router.get("/problems/{problem_id}")
async def get_problem(
    problem_id: str, 
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details of a single DSA problem if unlocked for the student."""
    try:
        prob = PROBLEMS.get(problem_id)
        if not prob:
            raise HTTPException(status_code=404, detail="Coding challenge not found")
            
        unlocked = await check_is_unlocked(problem_id, current_user.id, db)
        if not unlocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This challenge is locked. Complete the previous challenge to unlock it."
            )
            
        return {
            "id": problem_id,
            "title": prob["title"],
            "difficulty": prob["difficulty"],
            "description": prob["description"],
            "template": prob["template"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching problem: {str(e)}"
        )


@router.post("/submit", response_model=CodingSubmissionResponse)
async def submit_code(
    payload: CodingSubmissionCreate, 
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes coding test submission and saves execution details in PostgreSQL."""
    try:
        prob = PROBLEMS.get(payload.problem_id)
        if not prob:
            raise HTTPException(status_code=404, detail="Coding challenge not found")
            
        # Verify unlock progression to block skipping attempts
        unlocked = await check_is_unlocked(payload.problem_id, current_user.id, db)
        if not unlocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This challenge is locked. Complete the previous challenge first."
            )
            
        # Execute code in isolated python sandbox
        run_result = run_code_sandbox(payload.problem_id, payload.code, payload.language)
        
        # Save submission
        submission_doc = Submission(
            user_id=current_user.id,
            problem_id=payload.problem_id,
            language=payload.language,
            code=payload.code,
            status=run_result["status"],
            space_complexity=run_result["space_complexity"],
            time_complexity=run_result["time_complexity"],
            feedback=run_result["feedback"],
            date=datetime.now(timezone.utc)
        )
        db.add(submission_doc)
        await db.flush() # Populate submission_doc.id
        
        # Update profile score if they passed
        if run_result["status"] == "Pass":
            score_gain = 10.0
            if prob["difficulty"] == "Medium":
                score_gain = 20.0
            elif prob["difficulty"] == "Hard":
                score_gain = 30.0
                
            # Update user profile score
            user_stmt = select(User).where(User.id == current_user.id)
            user_result = await db.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()
            if db_user:
                db_user.profile_score = (db_user.profile_score or 0.0) + score_gain
                db.add(db_user)
                
        await db.commit()
        
        return CodingSubmissionResponse(
            id=str(submission_doc.id),
            user_id=str(current_user.id),
            problem_id=payload.problem_id,
            language=payload.language,
            code=payload.code,
            status=run_result["status"],
            space_complexity=run_result["space_complexity"],
            time_complexity=run_result["time_complexity"],
            feedback=run_result["feedback"],
            date=submission_doc.date
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting code: {str(e)}"
        )


@router.get("/submissions", response_model=List[CodingSubmissionResponse])
async def get_user_submissions(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch coding submission history for the logged-in user from PostgreSQL."""
    try:
        stmt = select(Submission).where(Submission.user_id == current_user.id).order_by(desc(Submission.date))
        result = await db.execute(stmt)
        submissions = result.scalars().all()
        
        return [
            CodingSubmissionResponse(
                id=str(sub.id),
                user_id=str(sub.user_id),
                problem_id=sub.problem_id,
                language=sub.language,
                code=sub.code,
                status=sub.status,
                space_complexity=sub.space_complexity or "N/A",
                time_complexity=sub.time_complexity or "N/A",
                feedback=sub.feedback or "",
                date=sub.date
            )
            for sub in submissions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching submissions: {str(e)}"
        )
