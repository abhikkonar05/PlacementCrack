from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, ATSCheckResult
from app.database import ats_checks_collection, users_collection
from app.ai.ats_evaluator import extract_text_from_pdf, evaluate_resume

router = APIRouter(prefix="/ats", tags=["ATS Resume Checker"])

@router.post("/check", response_model=ATSCheckResult)
async def check_resume(
    role: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Parses PDF resume, evaluates ATS compatibility score for target role, and saves feedback."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF file format is supported"
        )
        
    try:
        # Read file bytes
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
        check_doc = {
            "user_id": current_user.id,
            "role": role,
            "score": eval_result["score"],
            "matched_keywords": eval_result["matched_keywords"],
            "missing_keywords": eval_result["missing_keywords"],
            "suggestions": eval_result["suggestions"],
            "date": datetime.now(timezone.utc)
        }
        
        result = await ats_checks_collection.insert_one(check_doc)
        doc_id = str(result.inserted_id)
        
        # Increment profile score by score / 10
        score_gain = round(eval_result["score"] / 10.0, 1)
        await users_collection.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$inc": {"profile_score": score_gain}}
        )
        
        return ATSCheckResult(
            id=doc_id,
            user_id=current_user.id,
            score=eval_result["score"],
            matched_keywords=eval_result["matched_keywords"],
            missing_keywords=eval_result["missing_keywords"],
            suggestions=eval_result["suggestions"],
            date=check_doc["date"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume processing: {str(e)}"
        )

@router.get("/history", response_model=List[ATSCheckResult])
async def get_ats_history(current_user: UserResponse = Depends(get_current_user)):
    """Retrieve ATS resume check history for the logged-in user."""
    try:
        cursor = ats_checks_collection.find({"user_id": current_user.id}).sort("date", -1)
        history = []
        async for doc in cursor:
            history.append(ATSCheckResult(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                score=doc["score"],
                matched_keywords=doc["matched_keywords"],
                missing_keywords=doc["missing_keywords"],
                suggestions=doc["suggestions"],
                date=doc["date"]
            ))
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ATS history: {str(e)}"
        )
