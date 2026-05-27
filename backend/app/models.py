import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    university = Column(String(150), default="Not Specified")
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    profile_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    ats_checks = relationship("ATSCheck", back_populates="user", cascade="all, delete-orphan")
    aptitude_sessions = relationship("AptitudeSession", back_populates="user", cascade="all, delete-orphan")
    login_activities = relationship("LoginActivity", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    student_key = relationship("StudentKey", back_populates="user", uselist=False, cascade="all, delete-orphan")


class OTP(Base):
    __tablename__ = "otp_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    otp = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StudentKey(Base):
    __tablename__ = "student_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    student_key = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="student_key")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class DSAProblem(Base):
    __tablename__ = "dsa_problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    difficulty = Column(String(50), nullable=False)
    topic = Column(String(100), nullable=False)
    platform = Column(String(100), nullable=False)
    link = Column(String(512), unique=True, index=True, nullable=False)
    tags = Column(JSON, nullable=True)  # Store tags list as JSON
    company_tags = Column(JSON, nullable=True)  # Store company tags list as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AptitudeQuestion(Base):
    __tablename__ = "aptitude_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # Store list of options as JSON
    answer = Column(String(100), nullable=False)
    explanation = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    interview_type = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    opportunity_type = Column(String(100), nullable=False)
    eligibility = Column(String(255), nullable=True)
    deadline = Column(String(100), nullable=True)
    apply_link = Column(String(512), unique=True, index=True, nullable=False)
    location = Column(String(255), nullable=True)
    logo = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    problem_id = Column(String(100), index=True, nullable=False)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)  # "Pass", "Fail", "Error"
    space_complexity = Column(String(50), nullable=True)
    time_complexity = Column(String(50), nullable=True)
    feedback = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="submissions")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(100), nullable=False)
    category = Column(String(100), default="General", nullable=False)
    questions = Column(JSON, nullable=False)  # List of questions
    answers = Column(JSON, nullable=False)  # List of answers
    current_question_index = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    feedback = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="interviews")


class AptitudeSession(Base):
    __tablename__ = "aptitude_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    track = Column(String(100), nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    score = Column(Float, default=0.0, nullable=False)  # Percentage score
    feedback = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="aptitude_sessions")


class ATSCheck(Base):
    __tablename__ = "ats_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(100), nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    matched_keywords = Column(JSON, nullable=True)
    missing_keywords = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="ats_checks")


class LoginActivity(Base):
    __tablename__ = "login_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    login_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    user = relationship("User", back_populates="login_activities")


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSON, nullable=False)  # JSON structure containing steps/phases
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
