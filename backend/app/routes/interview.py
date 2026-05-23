from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, MockInterviewStart, InterviewAnswerSubmit, MockInterviewSession
from app.database import interviews_collection, users_collection
from app.ai.mock_interview import get_interview_questions, evaluate_full_interview
from app.ai.huggingface_client import is_huggingface_enabled, transcribe_audio_with_huggingface

router = APIRouter(prefix="/interview", tags=["Mock Interview"])

@router.post("/transcribe")
async def transcribe_interview_audio(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribes recorded interview audio through a Hugging Face ASR model."""
    try:
        if not is_huggingface_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hugging Face is not configured. Add HUGGINGFACE_API_TOKEN to enable voice transcription."
            )

        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio upload")

        transcript = await transcribe_audio_with_huggingface(audio_bytes, file.content_type or "audio/webm")
        if not transcript:
            raise HTTPException(status_code=502, detail="Could not transcribe audio. Try again or type your answer.")

        return {
            "transcript": transcript,
            "user_id": current_user.id
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {str(e)}"
        )

@router.post("/start", response_model=MockInterviewSession)
async def start_interview(
    payload: MockInterviewStart, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Starts a new mock interview session for a selected engineering role."""
    try:
        questions = await get_interview_questions(payload.role)
        
        interview_doc = {
            "user_id": current_user.id,
            "role": payload.role,
            "questions": questions,
            "answers": ["" for _ in questions], # empty answer placeholders
            "current_question_index": 0,
            "completed": False,
            "score": 0.0,
            "feedback": None,
            "date": datetime.now(timezone.utc)
        }
        
        result = await interviews_collection.insert_one(interview_doc)
        doc_id = str(result.inserted_id)
        
        return MockInterviewSession(
            id=doc_id,
            role=payload.role,
            questions=questions,
            answers=interview_doc["answers"],
            current_question_index=0,
            completed=False,
            score=0.0,
            feedback=None,
            date=interview_doc["date"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting interview: {str(e)}"
        )

@router.post("/submit-answer", response_model=MockInterviewSession)
async def submit_answer(
    payload: InterviewAnswerSubmit,
    current_user: UserResponse = Depends(get_current_user)
):
    """Submits answer for current question, handles progression, and runs final AI scorecard evaluation on completion."""
    try:
        # Find session
        if not ObjectId.is_valid(payload.interview_id):
            raise HTTPException(status_code=400, detail="Invalid interview ID format")
            
        session = await interviews_collection.find_one({
            "_id": ObjectId(payload.interview_id),
            "user_id": current_user.id
        })
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
            
        if session.get("completed"):
            raise HTTPException(status_code=400, detail="This interview session is already completed")
            
        questions = session["questions"]
        q_index = payload.question_index
        
        if q_index < 0 or q_index >= len(questions):
            raise HTTPException(status_code=400, detail="Invalid question index")
            
        # Update answer in answers array
        answers = session["answers"]
        answers[q_index] = payload.answer
        
        next_index = q_index + 1
        completed = next_index >= len(questions)
        
        update_data = {
            "answers": answers,
            "current_question_index": next_index if not completed else q_index,
            "completed": completed
        }
        
        # If completed, run final AI evaluation
        score = 0.0
        feedback = ""
        if completed:
            score, evaluation_details = await evaluate_full_interview(session["role"], questions, answers)
            update_data["score"] = score
            update_data["feedback"] = feedback = f"Detailed Breakdown:\n" + "\n".join([
                f"\nQ{item['question_number']}: {item['question']}\nCandidate: {item['answer']}\nScore: {item['score']}/100\nFeedback: {item['feedback']}\n"
                for item in evaluation_details
            ])
            
            # Increment user's profile score based on interview performance
            # User gets average_score / 5 points added to profile score
            score_gain = round(score / 5.0, 1)
            await users_collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$inc": {"profile_score": score_gain}}
            )
            
        await interviews_collection.update_one(
            {"_id": ObjectId(payload.interview_id), "user_id": current_user.id},
            {"$set": update_data}
        )
        
        return MockInterviewSession(
            id=payload.interview_id,
            role=session["role"],
            questions=questions,
            answers=answers,
            current_question_index=next_index if not completed else q_index,
            completed=completed,
            score=score if completed else 0.0,
            feedback=feedback if completed else None,
            date=session["date"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting answer: {str(e)}"
        )

@router.get("/session/{interview_id}", response_model=MockInterviewSession)
async def get_interview_session(
    interview_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve details and progress of a mock interview session by ID."""
    try:
        if not ObjectId.is_valid(interview_id):
            raise HTTPException(status_code=400, detail="Invalid interview ID format")
            
        session = await interviews_collection.find_one({
            "_id": ObjectId(interview_id),
            "user_id": current_user.id
        })
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
            
        return MockInterviewSession(
            id=str(session["_id"]),
            role=session["role"],
            questions=session["questions"],
            answers=session["answers"],
            current_question_index=session["current_question_index"],
            completed=session["completed"],
            score=session["score"],
            feedback=session.get("feedback"),
            date=session["date"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interview session: {str(e)}"
        )

@router.get("/history", response_model=List[MockInterviewSession])
async def get_interview_history(current_user: UserResponse = Depends(get_current_user)):
    """Retrieve mock interview history for the logged-in user."""
    try:
        cursor = interviews_collection.find({"user_id": current_user.id}).sort("date", -1)
        history = []
        async for doc in cursor:
            history.append(MockInterviewSession(
                id=str(doc["_id"]),
                role=doc["role"],
                questions=doc["questions"],
                answers=doc["answers"],
                current_question_index=doc["current_question_index"],
                completed=doc["completed"],
                score=doc["score"],
                feedback=doc.get("feedback"),
                date=doc["date"]
            ))
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interview history: {str(e)}"
        )
