from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
import re

from app.auth.router import get_current_user
from app.schemas import UserResponse
from app.database import db

router = APIRouter(tags=["Scraped Placement Prep Material"])

# Database handles
dsa_problems_collection = db["dsa_problems"]
roadmaps_collection = db["roadmaps"]
aptitude_questions_collection = db["aptitude_questions"]
interview_questions_collection = db["interview_questions"]
opportunities_collection = db["opportunities"]

@router.get("/software-development/questions")
async def get_dsa_questions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by: 'Beginner', 'Intermediate', 'Advanced'"),
    topic: Optional[str] = Query(None, description="Filter by topic (e.g., 'Arrays', 'Strings', 'Trees')"),
    search: Optional[str] = Query(None, description="Search keyword in title or tags"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve scraped DSA coding questions with pagination and filters."""
    try:
        query = {}
        if difficulty:
            query["difficulty"] = difficulty
        if topic:
            query["topic"] = topic
        if search:
            # Case-insensitive regex search
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}},
                {"company_tags": {"$regex": search, "$options": "i"}}
            ]

        total_count = await dsa_problems_collection.count_documents(query)
        cursor = dsa_problems_collection.find(query).skip((page - 1) * limit).limit(limit)
        
        problems = []
        async for doc in cursor:
            problems.append({
                "id": str(doc["_id"]),
                "title": doc["title"],
                "difficulty": doc["difficulty"],
                "topic": doc["topic"],
                "platform": doc["platform"],
                "link": doc["link"],
                "tags": doc.get("tags", []),
                "company_tags": doc.get("company_tags", [])
            })
            
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": problems
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving coding questions: {str(e)}"
        )

@router.get("/software-development/roadmaps")
async def get_roadmaps(
    current_user: UserResponse = Depends(get_current_user)
):
    """Fetch structured learning roadmaps for major dev roles (Frontend, Backend, DevOps)."""
    try:
        cursor = roadmaps_collection.find({})
        roadmaps = []
        async for doc in cursor:
            roadmaps.append({
                "id": str(doc["_id"]),
                "role": doc["role"],
                "description": doc["description"],
                "steps": doc.get("steps", [])
            })
        return {
            "success": True,
            "roadmaps": roadmaps
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Fetch paginated practice aptitude questions with detailed step-by-step explanations."""
    try:
        query = {}
        if category:
            query["category"] = category
        if difficulty:
            query["difficulty"] = difficulty
        if search:
            query["question"] = {"$regex": search, "$options": "i"}

        total_count = await aptitude_questions_collection.count_documents(query)
        cursor = aptitude_questions_collection.find(query).skip((page - 1) * limit).limit(limit)
        
        questions = []
        async for doc in cursor:
            questions.append({
                "id": str(doc["_id"]),
                "question": doc["question"],
                "options": doc["options"],
                "answer": doc["answer"],
                "explanation": doc["explanation"],
                "category": doc["category"],
                "difficulty": doc["difficulty"]
            })
            
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": questions
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve company-wise interview questions and candidate experience logs."""
    try:
        query = {}
        if interview_type:
            query["interview_type"] = interview_type
        if company:
            query["company_name"] = {"$regex": company, "$options": "i"}
        if search:
            query["question"] = {"$regex": search, "$options": "i"}

        total_count = await interview_questions_collection.count_documents(query)
        cursor = interview_questions_collection.find(query).skip((page - 1) * limit).limit(limit)
        
        questions = []
        async for doc in cursor:
            questions.append({
                "id": str(doc["_id"]),
                "company_name": doc["company_name"],
                "role": doc["role"],
                "interview_type": doc["interview_type"],
                "question": doc["question"],
                "answer": doc["answer"],
                "experience": doc.get("experience", ""),
                "category": doc.get("category", "")
            })
            
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "questions": questions
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
    opportunity_type: Optional[str] = Query(None, description="Filter by: 'Internship', 'Hackathon', 'Coding Contest', 'Open-Source Program', 'Remote Job'"),
    search: Optional[str] = Query(None, description="Search term in title or company"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Fetch active student opportunities (hackathons, contests, internships, remote jobs)."""
    try:
        query = {"is_active": True}
        if opportunity_type:
            query["opportunity_type"] = opportunity_type
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}}
            ]

        total_count = await opportunities_collection.count_documents(query)
        cursor = opportunities_collection.find(query).skip((page - 1) * limit).limit(limit)
        
        opportunities = []
        async for doc in cursor:
            opportunities.append({
                "id": str(doc["_id"]),
                "title": doc["title"],
                "company": doc["company"],
                "opportunity_type": doc["opportunity_type"],
                "eligibility": doc.get("eligibility", "Open to all"),
                "deadline": doc["deadline"],
                "apply_link": doc["apply_link"],
                "location": doc.get("location", "Remote"),
                "logo": doc.get("logo", "")
            })
            
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving opportunities: {str(e)}"
        )
