from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.auth.router import get_current_user
from app.schemas import UserResponse
from app.models import Submission, InterviewSession, AptitudeSession, ATSCheck, User
from app.sandbox.code_runner import PROBLEMS
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compiles all preparation metrics, unlock levels, and recent activities for the user dashboard."""
    try:
        # 1. Attempt counts
        submissions_count_query = select(func.count(Submission.id)).where(Submission.user_id == current_user.id)
        submissions_count = (await db.execute(submissions_count_query)).scalar() or 0

        interviews_count_query = select(func.count(InterviewSession.id)).where(
            InterviewSession.user_id == current_user.id, InterviewSession.completed == True
        )
        interviews_count = (await db.execute(interviews_count_query)).scalar() or 0

        aptitude_count_query = select(func.count(AptitudeSession.id)).where(AptitudeSession.user_id == current_user.id)
        aptitude_count = (await db.execute(aptitude_count_query)).scalar() or 0

        ats_count_query = select(func.count(ATSCheck.id)).where(ATSCheck.user_id == current_user.id)
        ats_count = (await db.execute(ats_count_query)).scalar() or 0

        total_attempts = submissions_count + interviews_count + aptitude_count

        # 2. Coding progression & locks
        solved_coding_query = select(func.count(func.distinct(Submission.problem_id))).where(
            Submission.user_id == current_user.id, Submission.status == "Pass"
        )
        solved_coding_count = (await db.execute(solved_coding_query)).scalar() or 0

        problem_keys = list(PROBLEMS.keys())
        unlocked_problems = []
        for i, pk in enumerate(problem_keys):
            if i == 0:
                unlocked_problems.append(pk)
            else:
                prev_pk = problem_keys[i-1]
                check_query = select(Submission.id).where(
                    Submission.user_id == current_user.id,
                    Submission.problem_id == prev_pk,
                    Submission.status == "Pass"
                ).limit(1)
                has_passed = (await db.execute(check_query)).scalar_one_or_none() is not None
                if has_passed:
                    unlocked_problems.append(pk)
                else:
                    break

        progress_percentage = round((solved_coding_count / len(problem_keys)) * 100.0, 1) if problem_keys else 0.0

        # 3. Aptitude & Interviews average scores
        aptitude_avg_query = select(func.avg(AptitudeSession.score)).where(AptitudeSession.user_id == current_user.id)
        aptitude_avg = (await db.execute(aptitude_avg_query)).scalar() or 0.0

        interview_avg_query = select(func.avg(InterviewSession.score)).where(
            InterviewSession.user_id == current_user.id, InterviewSession.completed == True
        )
        interview_avg = (await db.execute(interview_avg_query)).scalar() or 0.0

        # Latest records for immediate widgets
        latest_interview_query = select(InterviewSession).where(
            InterviewSession.user_id == current_user.id, InterviewSession.completed == True
        ).order_by(desc(InterviewSession.date)).limit(1)
        latest_interview = (await db.execute(latest_interview_query)).scalar_one_or_none()

        latest_ats_query = select(ATSCheck).where(ATSCheck.user_id == current_user.id).order_by(desc(ATSCheck.date)).limit(1)
        latest_ats = (await db.execute(latest_ats_query)).scalar_one_or_none()

        # 4. Compiling chronological activity log
        recent_activities = []

        recent_submissions = (await db.execute(
            select(Submission).where(Submission.user_id == current_user.id).order_by(desc(Submission.date)).limit(3)
        )).scalars().all()
        for s in recent_submissions:
            prob_title = PROBLEMS.get(s.problem_id, {}).get("title", s.problem_id)
            recent_activities.append({
                "type": "Coding Sandbox",
                "title": f"Submitted solution for {prob_title}",
                "detail": f"Status: {s.status}",
                "date": s.date
            })

        recent_interviews = (await db.execute(
            select(InterviewSession).where(
                InterviewSession.user_id == current_user.id, InterviewSession.completed == True
            ).order_by(desc(InterviewSession.date)).limit(3)
        )).scalars().all()
        for ri in recent_interviews:
            recent_activities.append({
                "type": "Mock Interview",
                "title": f"Completed {ri.role} mock interview",
                "detail": f"Score: {ri.score}/100",
                "date": ri.date
            })

        recent_aptitude = (await db.execute(
            select(AptitudeSession).where(AptitudeSession.user_id == current_user.id).order_by(desc(AptitudeSession.date)).limit(3)
        )).scalars().all()
        for ra in recent_aptitude:
            recent_activities.append({
                "type": "Aptitude Test",
                "title": f"Attempted {ra.track} Ability test",
                "detail": f"Accuracy: {ra.correct_answers}/{ra.total_questions} ({ra.score}%)",
                "date": ra.date
            })

        # Sort activities descending by date
        recent_activities.sort(key=lambda x: x["date"], reverse=True)
        recent_activities = recent_activities[:5]

        # User's current readiness score
        user_query = select(User.profile_score).where(User.id == current_user.id)
        user_score = (await db.execute(user_query)).scalar() or 0.0

        return {
            "success": True,
            "total_attempts": total_attempts,
            "profile_score": user_score,
            "coding": {
                "solved_challenges": solved_coding_count,
                "total_challenges": len(problem_keys),
                "unlocked_problems": unlocked_problems,
                "progress_percentage": progress_percentage
            },
            "aptitude": {
                "tests_attempted": aptitude_count,
                "average_score": round(float(aptitude_avg), 1)
            },
            "interview": {
                "interviews_attempted": interviews_count,
                "average_score": round(float(interview_avg), 1),
                "latest_score": latest_interview.score if latest_interview else 0.0,
                "latest_feedback": latest_interview.feedback if latest_interview else None
            },
            "ats": {
                "checks_count": ats_count,
                "latest_score": latest_ats.score if latest_ats else 0.0
            },
            "latest_activities": [
                {
                    "type": act["type"],
                    "title": act["title"],
                    "detail": act["detail"],
                    "date": act["date"].isoformat()
                }
                for act in recent_activities
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error compiling dashboard: {str(e)}"
        )
