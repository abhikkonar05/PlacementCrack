from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, CodingSubmissionCreate, CodingSubmissionResponse
from app.database import submissions_collection, users_collection
from app.sandbox.code_runner import PROBLEMS, run_code_sandbox

router = APIRouter(prefix="/coding", tags=["Coding Test"])

@router.get("/problems")
async def get_problems(current_user: UserResponse = Depends(get_current_user)):
    """Fetch the list of available DSA programming challenges."""
    try:
        problems_list = []
        for pid, prob in PROBLEMS.items():
            problems_list.append({
                "id": pid,
                "title": prob["title"],
                "difficulty": prob["difficulty"],
                "description": prob["description"],
                "template": prob["template"]
            })
        return problems_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching problems: {str(e)}"
        )

@router.get("/problems/{problem_id}")
async def get_problem(problem_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Retrieve details of a single DSA problem by ID."""
    try:
        prob = PROBLEMS.get(problem_id)
        if not prob:
            raise HTTPException(status_code=404, detail="Coding challenge not found")
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Compile, run and score the coding test submission in the python sandbox."""
    try:
        prob = PROBLEMS.get(payload.problem_id)
        if not prob:
            raise HTTPException(status_code=404, detail="Coding challenge not found")
            
        # Execute code in sandbox
        run_result = run_code_sandbox(payload.problem_id, payload.code, payload.language)
        
        # Save submission in database
        submission_doc = {
            "user_id": current_user.id,
            "problem_id": payload.problem_id,
            "language": payload.language,
            "code": payload.code,
            "status": run_result["status"],
            "space_complexity": run_result["space_complexity"],
            "time_complexity": run_result["time_complexity"],
            "feedback": run_result["feedback"],
            "date": datetime.now(timezone.utc)
        }
        
        result = await submissions_collection.insert_one(submission_doc)
        submission_id = str(result.inserted_id)
        
        # Update user's profile score if they passed
        if run_result["status"] == "Pass":
            score_gain = 10.0
            if prob["difficulty"] == "Medium":
                score_gain = 20.0
            elif prob["difficulty"] == "Hard":
                score_gain = 30.0
                
            # Update user profile score in database
            await users_collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$inc": {"profile_score": score_gain}}
            )
            
        return CodingSubmissionResponse(
            id=submission_id,
            user_id=current_user.id,
            problem_id=payload.problem_id,
            language=payload.language,
            code=payload.code,
            status=run_result["status"],
            space_complexity=run_result["space_complexity"],
            time_complexity=run_result["time_complexity"],
            feedback=run_result["feedback"],
            date=submission_doc["date"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting code: {str(e)}"
        )

@router.get("/submissions", response_model=List[CodingSubmissionResponse])
async def get_user_submissions(current_user: UserResponse = Depends(get_current_user)):
    """Fetch all coding submission history for the logged-in user."""
    try:
        cursor = submissions_collection.find({"user_id": current_user.id}).sort("date", -1)
        submissions = []
        async for doc in cursor:
            submissions.append(CodingSubmissionResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                problem_id=doc["problem_id"],
                language=doc["language"],
                code=doc["code"],
                status=doc["status"],
                space_complexity=doc["space_complexity"],
                time_complexity=doc["time_complexity"],
                feedback=doc["feedback"],
                date=doc["date"]
            ))
        return submissions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching submissions: {str(e)}"
        )
