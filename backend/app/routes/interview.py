from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from datetime import datetime, timezone
from typing import List

from app.auth.router import get_current_user
from app.schemas import UserResponse, MockInterviewStart, InterviewAnswerSubmit, MockInterviewSession
from app.database import get_db
from app.models import InterviewSession, User
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
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Starts a new mock interview session for a selected engineering role."""
    try:
        questions = await get_interview_questions(payload.role)
        category = payload.category or "General"
        
        interview_doc = InterviewSession(
            user_id=uuid.UUID(current_user.id),
            role=payload.role,
            category=category,
            questions=questions,
            answers=["" for _ in questions], # empty answer placeholders
            current_question_index=0,
            completed=False,
            score=0.0,
            feedback=None,
            date=datetime.now(timezone.utc)
        )
        db.add(interview_doc)
        await db.commit()
        
        return MockInterviewSession(
            id=str(interview_doc.id),
            role=interview_doc.role,
            category=interview_doc.category,
            questions=interview_doc.questions,
            answers=interview_doc.answers,
            current_question_index=0,
            completed=False,
            score=0.0,
            feedback=None,
            date=interview_doc.date
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting interview: {str(e)}"
        )


@router.post("/submit-answer", response_model=MockInterviewSession)
async def submit_answer(
    payload: InterviewAnswerSubmit,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits answer for current question, handles progression, and runs final AI scorecard evaluation on completion."""
    try:
        # Find session
        try:
            session_id = uuid.UUID(payload.interview_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid interview ID format")
            
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == uuid.UUID(current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
            
        if session.completed:
            raise HTTPException(status_code=400, detail="This interview session is already completed")
            
        questions = session.questions
        q_index = payload.question_index
        
        if q_index < 0 or q_index >= len(questions):
            raise HTTPException(status_code=400, detail="Invalid question index")
            
        # Update answer in answers array
        answers = list(session.answers)
        answers[q_index] = payload.answer
        
        next_index = q_index + 1
        completed = next_index >= len(questions)
        
        session.answers = answers
        session.current_question_index = next_index if not completed else q_index
        session.completed = completed
        
        # If completed, run final AI evaluation
        score = 0.0
        feedback = ""
        if completed:
            score, evaluation_details = await evaluate_full_interview(session.role, questions, answers)
            session.score = score
            session.feedback = feedback = f"Detailed Breakdown:\n" + "\n".join([
                f"\nQ{item['question_number']}: {item['question']}\nCandidate: {item['answer']}\nScore: {item['score']}/100\nFeedback: {item['feedback']}\n"
                for item in evaluation_details
            ])
            
            # Increment user's profile score based on interview performance
            # User gets average_score / 5 points added to profile score
            score_gain = round(score / 5.0, 1)
            user_stmt = select(User).where(User.id == uuid.UUID(current_user.id))
            user_result = await db.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()
            if db_user:
                db_user.profile_score = (db_user.profile_score or 0.0) + score_gain
                db.add(db_user)
                
        db.add(session)
        await db.commit()
        
        return MockInterviewSession(
            id=str(session.id),
            role=session.role,
            category=session.category,
            questions=questions,
            answers=answers,
            current_question_index=session.current_question_index,
            completed=session.completed,
            score=session.score,
            feedback=session.feedback,
            date=session.date
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting answer: {str(e)}"
        )


@router.get("/session/{interview_id}", response_model=MockInterviewSession)
async def get_interview_session(
    interview_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details and progress of a mock interview session by ID."""
    try:
        try:
            session_id = uuid.UUID(interview_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid interview ID format")
            
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == uuid.UUID(current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
            
        return MockInterviewSession(
            id=str(session.id),
            role=session.role,
            category=session.category,
            questions=session.questions,
            answers=session.answers,
            current_question_index=session.current_question_index,
            completed=session.completed,
            score=session.score,
            feedback=session.feedback,
            date=session.date
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interview session: {str(e)}"
        )


@router.get("/history", response_model=List[MockInterviewSession])
async def get_interview_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve mock interview history for the logged-in user."""
    try:
        stmt = select(InterviewSession).where(
            InterviewSession.user_id == uuid.UUID(current_user.id)
        ).order_by(desc(InterviewSession.date))
        result = await db.execute(stmt)
        history_records = result.scalars().all()
        
        return [
            MockInterviewSession(
                id=str(doc.id),
                role=doc.role,
                category=doc.category,
                questions=doc.questions,
                answers=doc.answers,
                current_question_index=doc.current_question_index,
                completed=doc.completed,
                score=doc.score,
                feedback=doc.feedback,
                date=doc.date
            )
            for doc in history_records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interview history: {str(e)}"
        )
