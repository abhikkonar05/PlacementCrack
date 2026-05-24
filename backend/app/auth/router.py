from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import random
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config import settings
from app.database import get_db
from app.models import User, OTP, LoginKey, RefreshToken, LoginActivity
from app.schemas import (
    OTPSendRequest, 
    OTPVerifyRequest, 
    UserRegister, 
    UserLogin, 
    UserResponse, 
    Token, 
    TokenData
)
from app.auth.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.auth.email_service import send_otp_email, send_login_key_email
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Simple memory cache for Rate Limiting
rate_limit_store = {}

def check_rate_limit(key: str, max_requests: int = 3, window_seconds: int = 60) -> bool:
    """Sliding-window rate limiter for email addresses to block spam."""
    now = time.time()
    timestamps = rate_limit_store.get(key, [])
    # Filter timestamps older than the window
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        return True
    timestamps.append(now)
    rate_limit_store[key] = timestamps
    return False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(
    user: UserRegister, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
            
        # Check existing user by email
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email address is already registered."
                )
            else:
                # If existing user is unverified, remove so we can recreate it
                await db.delete(existing_user)
                await db.commit()
        
        # Save temporary unverified user in PostgreSQL
        hashed_password = get_password_hash(user.password)
        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            name=f"{user.first_name} {user.last_name}",
            university="Not Specified",
            email=user.email,
            phone=None,
            password_hash=hashed_password,
            is_verified=False,
            profile_score=0.0
        )
        db.add(new_user)
        await db.flush() # Populate new_user.id
        
        # Generate 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        
        # Upsert OTP record
        otp_stmt = select(OTP).where(OTP.email == user.email)
        otp_result = await db.execute(otp_stmt)
        existing_otp = otp_result.scalar_one_or_none()
        
        if existing_otp:
            existing_otp.otp = otp_code
            existing_otp.expires_at = expiry_time
            db.add(existing_otp)
        else:
            new_otp = OTP(
                email=user.email,
                otp=otp_code,
                expires_at=expiry_time
            )
            db.add(new_otp)
            
        await db.commit()
        
        # Send OTP in background
        background_tasks.add_task(send_otp_email, user.email, otp_code)
            
        return {
            "success": True, 
            "message": "OTP verification code sent to your email.", 
            "otp": otp_code if settings.DEVELOPER_MODE else None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )


@router.post("/verify-otp")
async def verify_otp(
    payload: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verify OTP
        otp_stmt = select(OTP).where(OTP.email == payload.email)
        otp_result = await db.execute(otp_stmt)
        otp_doc = otp_result.scalar_one_or_none()
        
        if not otp_doc or otp_doc.otp != payload.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code."
            )
            
        # Time validation
        now = datetime.now(timezone.utc)
        if otp_doc.expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )

        # Mark user verified
        user_stmt = select(User).where(User.email == payload.email)
        user_result = await db.execute(user_stmt)
        user_doc = user_result.scalar_one_or_none()
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found."
            )
            
        user_doc.is_verified = True
        db.add(user_doc)
        
        # Delete verified OTP record
        await db.delete(otp_doc)
        await db.commit()
        
        return {
            "success": True,
            "message": "Email verified successfully. You can now login."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP Verification error: {str(e)}"
        )


@router.post("/resend-otp")
async def resend_otp(
    payload: OTPSendRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        if check_rate_limit(payload.email, max_requests=3, window_seconds=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please wait a minute before requesting another."
            )

        # Check if user exists
        user_stmt = select(User).where(User.email == payload.email)
        user_result = await db.execute(user_stmt)
        existing_user = user_result.scalar_one_or_none()
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No registration request found for this email."
            )
            
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already verified."
            )
        
        # Generate new 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        
        # Update OTP in database
        otp_stmt = select(OTP).where(OTP.email == payload.email)
        otp_result = await db.execute(otp_stmt)
        existing_otp = otp_result.scalar_one_or_none()
        
        if existing_otp:
            existing_otp.otp = otp_code
            existing_otp.expires_at = expiry_time
            db.add(existing_otp)
        else:
            new_otp = OTP(email=payload.email, otp=otp_code, expires_at=expiry_time)
            db.add(new_otp)
            
        await db.commit()
        
        # Resend OTP in background
        background_tasks.add_task(send_otp_email, payload.email, otp_code)
            
        return {
            "success": True, 
            "message": "Verification code resent successfully.", 
            "otp": otp_code if settings.DEVELOPER_MODE else None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend OTP error: {str(e)}"
        )


@router.post("/login")
async def login(
    credentials: UserLogin, 
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_stmt = select(User).where(User.email == credentials.email)
        user_result = await db.execute(user_stmt)
        user_doc = user_result.scalar_one_or_none()
        
        if not user_doc or not verify_password(credentials.password, user_doc.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email address or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user_doc.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your email is not verified yet. Please register again to verify."
            )
        
        now = datetime.now(timezone.utc)
        
        # STEP 1: Generate/Reuse and send verification login key
        if not credentials.login_key:
            # Check if there is an active valid login key
            key_stmt = select(LoginKey).where(LoginKey.email == credentials.email)
            key_result = await db.execute(key_stmt)
            existing_key = key_result.scalar_one_or_none()
            
            if existing_key and existing_key.expires_at.replace(tzinfo=timezone.utc) > now:
                # Reuse the active key
                login_key = existing_key.login_key
            else:
                # Generate new key
                first_name = user_doc.first_name or "User"
                first_char = first_name[0].upper() if first_name else "U"
                random_digits = f"{random.randint(1000, 9999)}"
                login_key = f"{first_char}{random_digits}"
                expiry_time = now + timedelta(minutes=3)
                
                if existing_key:
                    existing_key.login_key = login_key
                    existing_key.expires_at = expiry_time
                    db.add(existing_key)
                else:
                    new_key = LoginKey(
                        email=credentials.email,
                        login_key=login_key,
                        expires_at=expiry_time
                    )
                    db.add(new_key)
                    
                await db.commit()
            
            # Send login key via email
            first_name = user_doc.first_name or "User"
            background_tasks.add_task(send_login_key_email, credentials.email, first_name, login_key)
            
            return {
                "key_sent": True,
                "email": credentials.email,
                "login_key": login_key if settings.DEVELOPER_MODE else None
            }
            
        # STEP 2: Verify login key
        key_stmt = select(LoginKey).where(LoginKey.email == credentials.email)
        key_result = await db.execute(key_stmt)
        key_doc = key_result.scalar_one_or_none()
        
        if not key_doc or key_doc.login_key != credentials.login_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid unique login key."
            )
            
        # Time validation for login key
        if key_doc.expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login key has expired. Please log in again."
            )
            
        # Success! Log activity
        client_host = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("user-agent", "Unknown")
        activity = LoginActivity(
            user_id=user_doc.id,
            login_time=now,
            ip_address=client_host,
            user_agent=user_agent
        )
        db.add(activity)
        
        # Access and Refresh Tokens
        access_token = create_access_token(data={"sub": credentials.email})
        refresh_token = create_refresh_token(data={"sub": credentials.email})
        
        # Save refresh token in database
        refresh_expires = now + timedelta(days=7)
        new_refresh = RefreshToken(
            user_id=user_doc.id,
            token=refresh_token,
            expires_at=refresh_expires
        )
        db.add(new_refresh)
        
        await db.commit()
        
        user_resp = UserResponse(
            id=str(user_doc.id),
            first_name=user_doc.first_name,
            last_name=user_doc.last_name,
            name=user_doc.name,
            email=user_doc.email,
            university=user_doc.university,
            phone=user_doc.phone,
            is_verified=True,
            created_at=user_doc.created_at,
            profile_score=user_doc.profile_score or 0.0
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_resp
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/refresh")
async def refresh_session(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Regenerates a new access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_payload = jwt.decode(payload.refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = token_payload.get("sub")
        token_type: str = token_payload.get("type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
            
        # Verify in database
        stmt = select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
        result = await db.execute(stmt)
        token_doc = result.scalar_one_or_none()
        
        if not token_doc:
            raise credentials_exception
            
        now = datetime.now(timezone.utc)
        if token_doc.expires_at.replace(tzinfo=timezone.utc) < now:
            # Token expired, prune it
            await db.delete(token_doc)
            await db.commit()
            raise credentials_exception
            
        # Generate new access token
        access_token = create_access_token(data={"sub": email})
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh session error: {str(e)}"
        )


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email:
            # Delete active login keys and refresh tokens for this user
            user_stmt = select(User).where(User.email == email)
            user_result = await db.execute(user_stmt)
            user_doc = user_result.scalar_one_or_none()
            
            if user_doc:
                # Delete active refresh tokens
                await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_doc.id))
                # Delete active login keys
                await db.execute(delete(LoginKey).where(LoginKey.email == email))
                await db.commit()
        return {"success": True, "message": "Logged out successfully."}
    except Exception:
        return {"success": True, "message": "Logged out successfully."}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Dependency to retrieve the currently logged in user based on email session."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception
        
    try:
        user_stmt = select(User).where(User.email == token_data.email)
        user_result = await db.execute(user_stmt)
        user_doc = user_result.scalar_one_or_none()
        
        if user_doc is None or not user_doc.is_verified:
            raise credentials_exception
            
        return UserResponse(
            id=str(user_doc.id),
            first_name=user_doc.first_name,
            last_name=user_doc.last_name,
            name=user_doc.name,
            email=user_doc.email,
            university=user_doc.university,
            phone=user_doc.phone,
            is_verified=True,
            created_at=user_doc.created_at,
            profile_score=user_doc.profile_score or 0.0
        )
    except HTTPException as he:
        raise he
    except Exception:
        raise credentials_exception


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
