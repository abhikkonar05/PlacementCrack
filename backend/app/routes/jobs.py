from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional

from app.auth.router import get_current_user
from app.schemas import UserResponse
from app.scraper.job_scraper import get_jobs_by_role

router = APIRouter(prefix="/jobs", tags=["Job/Internship Finder"])

@router.get("")
async def get_jobs(
    role: Optional[str] = Query(None, description="Filter jobs by track: 'Data Science', 'AI/ML', 'Software Development'"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve scraped remote job and internship postings, filtered by candidate target role."""
    try:
        if role:
            jobs = get_jobs_by_role(role)
        else:
            # If no role specified, show all jobs
            from app.scraper.job_scraper import fetch_wewokremotely_jobs
            jobs = fetch_wewokremotely_jobs()
            
        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching jobs: {str(e)}"
        )
