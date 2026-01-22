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
    """
    OAuth2 compatible token login, get an access token and user information for future requests
    """
    try:
        logger.info(f"Login attempt for email: {form_data.username}")
        user = User.authenticate(db, email=form_data.username, password=form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for email: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION)
        token = security.create_access_token(user.id, expires_delta=access_token_expires)
        logger.info(f"Successful login for user: {user.id} ({user.email})")
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
    """
    Create new user.
    Returns user information only. Use /login endpoint to get authorization token.
    """
    try:
        logger.info(f"Registration attempt for email: {user_in.email}")
        user = User.get_by_email(db, email=user_in.email)
        if user:
            logger.warning(f"Registration failed: email already exists: {user_in.email}")
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        
        user = User.create(db, obj_in=user_in)
        logger.info(f"User registered successfully: {user.id} ({user.email})")

        # Queue background tasks (optional - don't fail if Celery is not running)
        try:
            send_welcome_email.delay(user.id)
            process_user_data.delay(user.id)
            logger.debug(f"Background tasks queued for user: {user.id}")
        except Exception as e:
            # Log but don't fail registration if Celery is not available
            logger.warning(
                f"Could not queue background tasks for user {user.id}",
                context={"error": str(e)},
            )

        # Example: Broadcast user created event (optional)
        try:
            event = UserCreated(user)
            broadcast().event(event)
            logger.debug(f"User created event broadcasted for user: {user.id}")
        except Exception as e:
            logger.warning(
                f"Could not broadcast event for user {user.id}",
                context={"error": str(e)},
            )

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
