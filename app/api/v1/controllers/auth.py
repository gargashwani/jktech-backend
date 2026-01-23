from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.broadcasting import broadcast
from app.core.database import get_db
from app.core.logging import get_logger
from app.events.user_events import UserCreated
from app.jobs.tasks import process_user_data, send_welcome_email
from app.models.user import User
from app.schemas.token import TokenWithUser
from app.schemas.user import UserCreate, UserResponse
from config import settings

router = APIRouter()
logger = get_logger("auth")


@router.post("/login", response_model=TokenWithUser)
def login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    try:
        logger.info(f"Login attempt: {form_data.username}")
        user = User.authenticate(db, email=form_data.username, password=form_data.password)
        if not user:
            logger.warning(f"Failed login: {form_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        expires = timedelta(minutes=settings.JWT_EXPIRATION)
        token = security.create_access_token(user.id, expires_delta=expires)
        logger.info(f"Login successful: {user.email}")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during login", e, context={"email": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    try:
        logger.info(f"Registration: {user_in.email}")
        existing = User.get_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        user = User.create(db, obj_in=user_in)
        logger.info(f"User registered: {user.email}")

        # Try to queue background tasks (don't fail if Celery is down)
        try:
            send_welcome_email.delay(user.id)
            process_user_data.delay(user.id)
        except Exception as e:
            logger.warning(f"Couldn't queue tasks: {e}")

        # Try to broadcast event
        try:
            broadcast().event(UserCreated(user))
        except Exception as e:
            logger.warning(f"Couldn't broadcast: {e}")

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error during registration",
            e,
            context={"email": user_in.email},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration",
        )
