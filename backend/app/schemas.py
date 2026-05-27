from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CAPTCHAGenerateResponse(BaseModel):
    captcha_id: str
    question: str  # e.g., "5 + 3 = ?"

class OTPSendRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    login_key: str

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    name: str
    email: EmailStr
    university: Optional[str] = "Not Specified"
    phone: Optional[str] = None
    is_verified: bool = False
    created_at: datetime
    profile_score: float = 0.0

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Coding schemas
class CodingSubmissionCreate(BaseModel):
    problem_id: str
    code: str
    language: str

class CodingSubmissionResponse(BaseModel):
    id: str
    user_id: str
    problem_id: str
    language: str
    code: str
    status: str  # "Pass" or "Fail" or "Error"
    space_complexity: str
    time_complexity: str
    feedback: str
    date: datetime

# Mock interview schemas
class MockInterviewStart(BaseModel):
    role: str # "Software Development", "Aptitude Test", "Mock Interview"
    category: Optional[str] = "General" # "HR", "Technical", "Behavioral"

class InterviewAnswerSubmit(BaseModel):
    interview_id: str
    question_index: int
    answer: str

class MockInterviewSession(BaseModel):
    id: str
    role: str
    category: str
    questions: List[str]
    answers: List[str]
    current_question_index: int
    completed: bool
    score: float
    feedback: Optional[str] = None
    date: datetime

# ATS checker schemas
class ATSCheckResult(BaseModel):
    id: str
    user_id: str
    score: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
    date: datetime

# Aptitude Test schemas
class AptitudeTestStart(BaseModel):
    track: str = "Quantitative" # "Quantitative", "Logical", "Verbal", "Mock Aptitude"

class AptitudeAnswerSubmit(BaseModel):
    test_id: str
    question_index: int
    selected_option: str # "A", "B", "C", "D" or empty for skip

class AptitudeTestResult(BaseModel):
    id: str
    user_id: str
    track: str
    total_questions: int
    correct_answers: int
    score: float  # Percentage
    feedback: str
    date: datetime

# Opportunities schemas
class OpportunityResponse(BaseModel):
    id: str
    title: str
    company: str
    url: str
    location: str
    logo: str
    date: str
    type: str # "Internship", "Hackathon", "Coding Contest", "Hiring Challenge", "Remote Job", "Open-Source"
    deadline: Optional[str] = "N/A"
    eligibility: Optional[str] = "Open to all"