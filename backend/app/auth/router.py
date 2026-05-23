from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import random
import time
from bson import ObjectId

from app.config import settings
from app.database import users_collection, otps_collection, login_keys_collection
from app.schemas import (
    OTPSendRequest, 
    OTPVerifyRequest, 
    UserRegister, 
    UserLogin, 
    UserResponse, 
    Token, 
    TokenData
)
from app.auth.security import verify_password, get_password_hash, create_access_token
from app.auth.email_service import send_otp_email, send_login_key_email

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

@router.post("/register")
async def register(user: UserRegister, background_tasks: BackgroundTasks):
    try:
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
            
        # Check existing user by email
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            if existing_user.get("is_verified"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email address is already registered."
                )
            else:
                # If existing user is unverified, remove so we can recreate it
                await users_collection.delete_one({"email": user.email})
        
        # Save temporary unverified user in MongoDB
        hashed_password = get_password_hash(user.password)
        user_dict = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": f"{user.first_name} {user.last_name}",
            "university": "Not Specified",
            "email": user.email,
            "phone": None,
            "password_hash": hashed_password,
            "is_verified": False,
            "created_at": datetime.now(timezone.utc),
            "profile_score": 0.0
        }
        
        await users_collection.insert_one(user_dict)
        
        # Generate 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        
        # Save OTP to database
        await otps_collection.update_one(
            {"email": user.email},
            {
                "$set": {
                    "otp": otp_code,
                    "expires_at": expiry_time
                }
            },
            upsert=True
        )
        
        # Send Resend OTP in background
        background_tasks.add_task(send_otp_email, user.email, otp_code)
            
        return {
            "success": True, 
            "message": "OTP verification code sent to your email.", 
            "otp": otp_code if settings.DEVELOPER_MODE else None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )

@router.post("/verify-otp")
async def verify_otp(payload: OTPVerifyRequest):
    try:
        # Verify OTP
        otp_doc = await otps_collection.find_one({"email": payload.email})
        if not otp_doc or otp_doc.get("otp") != payload.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code."
            )
            
        # Time validation
        now = datetime.now(timezone.utc)
        expires_at = otp_doc.get("expires_at")
        if expires_at and expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )

        # Mark user verified
        await users_collection.update_one(
            {"email": payload.email}, 
            {"$set": {"is_verified": True}}
        )
        
        # Delete verified OTP record
        await otps_collection.delete_one({"email": payload.email})
        
        return {
            "success": True,
            "message": "Email verified successfully. You can now login."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP Verification error: {str(e)}"
        )

@router.post("/resend-otp")
async def resend_otp(payload: OTPSendRequest, background_tasks: BackgroundTasks):
    try:
        # Check Rate Limiter (max 3 OTPs per email per minute)
        if check_rate_limit(payload.email, max_requests=3, window_seconds=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please wait a minute before requesting another."
            )

        # Check if user exists
        existing_user = await users_collection.find_one({"email": payload.email})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No registration request found for this email."
            )
            
        if existing_user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already verified."
            )
        
        # Generate new 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        
        # Update OTP in database
        await otps_collection.update_one(
            {"email": payload.email},
            {
                "$set": {
                    "otp": otp_code,
                    "expires_at": expiry_time
                }
            },
            upsert=True
        )
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend OTP error: {str(e)}"
        )

@router.post("/login")
async def login(credentials: UserLogin, background_tasks: BackgroundTasks):
    try:
        user_doc = await users_collection.find_one({"email": credentials.email})
        if not user_doc or not verify_password(credentials.password, user_doc.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email address or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user_doc.get("is_verified", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your email is not verified yet. Please register again to verify."
            )
        
        # STEP 1: If unique login key is NOT provided, generate and send it
        if not credentials.login_key:
            first_name = user_doc.get("first_name", "User")
            first_char = first_name[0].upper() if first_name else "U"
            random_digits = f"{random.randint(1000, 9999)}"
            login_key = f"{first_char}{random_digits}"
            
            # Store login key temporarily (expires in 3 minutes)
            expiry_time = datetime.now(timezone.utc) + timedelta(minutes=3)
            await login_keys_collection.update_one(
                {"email": credentials.email},
                {
                    "$set": {
                        "login_key": login_key,
                        "expires_at": expiry_time
                    }
                },
                upsert=True
            )
            
            # Send login key via Resend
            background_tasks.add_task(send_login_key_email, credentials.email, first_name, login_key)
            
            return {
                "key_sent": True,
                "email": credentials.email,
                "login_key": login_key if settings.DEVELOPER_MODE else None
            }
            
        # STEP 2: Verify login key
        key_doc = await login_keys_collection.find_one({"email": credentials.email})
        if not key_doc or key_doc.get("login_key") != credentials.login_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid unique login key."
            )
            
        # Time validation for login key
        now = datetime.now(timezone.utc)
        expires_at = key_doc.get("expires_at")
        if expires_at and expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login key has expired. Please log in again."
            )
            
        # Clean up login key after successful login
        await login_keys_collection.delete_one({"email": credentials.email})
        
        # Return JWT token
        user_resp = UserResponse(
            id=str(user_doc["_id"]),
            first_name=user_doc["first_name"],
            last_name=user_doc["last_name"],
            name=user_doc["name"],
            email=user_doc["email"],
            university=user_doc.get("university", "Not Specified"),
            phone=user_doc.get("phone"),
            is_verified=True,
            created_at=user_doc["created_at"],
            profile_score=user_doc.get("profile_score", 0.0)
        )
        
        access_token = create_access_token(data={"sub": credentials.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_resp
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email:
            # Clear active login keys for this user
            await login_keys_collection.delete_one({"email": email})
        return {"success": True, "message": "Logged out successfully."}
    except Exception:
        return {"success": True, "message": "Logged out successfully."}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
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
        user_doc = await users_collection.find_one({"email": token_data.email})
        if user_doc is None or not user_doc.get("is_verified", False):
            raise credentials_exception
            
        return UserResponse(
            id=str(user_doc["_id"]),
            first_name=user_doc["first_name"],
            last_name=user_doc["last_name"],
            name=user_doc["name"],
            email=user_doc["email"],
            university=user_doc.get("university", "Not Specified"),
            phone=user_doc.get("phone"),
            is_verified=True,
            created_at=user_doc["created_at"],
            profile_score=user_doc.get("profile_score", 0.0)
        )
    except HTTPException as he:
        raise he
    except Exception:
        raise credentials_exception

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
