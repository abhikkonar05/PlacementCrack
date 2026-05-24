from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from datetime import datetime, timezone

from app.auth.router import get_current_user
from app.schemas import UserResponse
from app.database import get_db
from app.models import DSAProblem, Roadmap, AptitudeQuestion, InterviewQuestion, Opportunity

router = APIRouter(tags=["Scraped Placement Prep Material"])


@router.get("/software-development/questions")
async def get_dsa_questions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by: 'Beginner', 'Intermediate', 'Advanced'"),
    topic: Optional[str] = Query(None, description="Filter by topic (e.g., 'Arrays', 'Strings', 'Trees')"),
    search: Optional[str] = Query(None, description="Search keyword in title or tags"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve scraped DSA coding questions with pagination and filters from PostgreSQL."""
    try:
        query = select(DSAProblem)
        count_query = select(func.count(DSAProblem.id))
        
        filters = []
        if difficulty:
            filters.append(DSAProblem.difficulty == difficulty)
        if topic:
            filters.append(DSAProblem.topic == topic)
        if search:
            # Case-insensitive like search
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    DSAProblem.title.ilike(search_pattern),
                    DSAProblem.topic.ilike(search_pattern)
                )
            )
            
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
            
        # Execute count
        total_count = (await db.execute(count_query)).scalar() or 0
        
        # Execute pagination
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        problems = result.scalars().all()
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "difficulty": doc.difficulty,
                    "topic": doc.topic,
                    "platform": doc.platform,
                    "link": doc.link,
                    "tags": doc.tags or [],
                    "company_tags": doc.company_tags or []
                }
                for doc in problems
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving coding questions: {str(e)}"
        )


@router.get("/software-development/roadmaps")
async def get_roadmaps(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch structured learning roadmaps for major dev roles (Frontend, Backend, DevOps)."""
    try:
        stmt = select(Roadmap)
        result = await db.execute(stmt)
        roadmaps_list = result.scalars().all()
        
        return {
            "success": True,
            "roadmaps": [
                {
                    "id": str(doc.id),
                    "role": doc.role,
                    "description": doc.description,
                    "steps": doc.steps or []
                }
                for doc in roadmaps_list
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving roadmaps: {str(e)}"
        )


@router.get("/aptitude/questions")
async def get_aptitude_questions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filter by: 'Quantitative', 'Logical', 'Verbal'"),
    difficulty: Optional[str] = Query(None, description="Filter by: 'Beginner', 'Intermediate', 'Advanced'"),
    search: Optional[str] = Query(None, description="Search term in question text"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch paginated practice aptitude questions with detailed explanations from PostgreSQL."""
    try:
        query = select(AptitudeQuestion)
        count_query = select(func.count(AptitudeQuestion.id))
        
        filters = []
        if category:
            filters.append(AptitudeQuestion.category == category)
        if difficulty:
            filters.append(AptitudeQuestion.difficulty == difficulty)
        if search:
            filters.append(AptitudeQuestion.question.ilike(f"%{search}%"))
            
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
            
        total_count = (await db.execute(count_query)).scalar() or 0
        
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        questions_list = result.scalars().all()
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": [
                {
                    "id": str(doc.id),
                    "question": doc.question,
                    "options": doc.options or [],
                    "answer": doc.answer,
                    "explanation": doc.explanation,
                    "category": doc.category,
                    "difficulty": doc.difficulty
                }
                for doc in questions_list
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving aptitude questions: {str(e)}"
        )


@router.get("/interview/questions")
async def get_interview_questions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    interview_type: Optional[str] = Query(None, description="Filter by: 'HR', 'Technical', 'Behavioral'"),
    company: Optional[str] = Query(None, description="Filter by specific company name"),
    search: Optional[str] = Query(None, description="Search keyword in question text"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve company-wise interview questions and experience logs from PostgreSQL."""
    try:
        query = select(InterviewQuestion)
        count_query = select(func.count(InterviewQuestion.id))
        
        filters = []
        if interview_type:
            filters.append(InterviewQuestion.interview_type == interview_type)
        if company:
            filters.append(InterviewQuestion.company_name.ilike(f"%{company}%"))
        if search:
            filters.append(InterviewQuestion.question.ilike(f"%{search}%"))
            
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
            
        total_count = (await db.execute(count_query)).scalar() or 0
        
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        questions_list = result.scalars().all()
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": [
                {
                    "id": str(doc.id),
                    "company_name": doc.company_name,
                    "role": doc.role,
                    "interview_type": doc.interview_type,
                    "question": doc.question,
                    "answer": doc.answer,
                    "experience": doc.experience or "",
                    "category": doc.category or ""
                }
                for doc in questions_list
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interview questions: {str(e)}"
        )


@router.get("/opportunities")
async def get_opportunities(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    opportunity_type: Optional[str] = Query(None, description="Filter by opportunity type"),
    search: Optional[str] = Query(None, description="Search term in title or company"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch active student opportunities (hackathons, contests, internships, remote jobs) from PostgreSQL."""
    try:
        query = select(Opportunity).where(Opportunity.is_active == True)
        count_query = select(func.count(Opportunity.id)).where(Opportunity.is_active == True)
        
        filters = []
        if opportunity_type:
            filters.append(Opportunity.opportunity_type == opportunity_type)
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Opportunity.title.ilike(search_pattern),
                    Opportunity.company.ilike(search_pattern)
                )
            )
            
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
            
        total_count = (await db.execute(count_query)).scalar() or 0
        
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        opportunities_list = result.scalars().all()
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "opportunities": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "company": doc.company,
                    "opportunity_type": doc.opportunity_type,
                    "eligibility": doc.eligibility or "Open to all",
                    "deadline": doc.deadline,
                    "apply_link": doc.apply_link,
                    "location": doc.location or "Remote",
                    "logo": doc.logo or ""
                }
                for doc in opportunities_list
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving opportunities: {str(e)}"
        )
