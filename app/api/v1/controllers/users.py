import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.broadcasting import broadcast
from app.core.cache import cache
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.policies import UserPolicy
from app.core.security import get_current_user
from app.events.user_events import UserDeleted, UserUpdated
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()
logger = get_logger("users")


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own user (with cache invalidation and broadcasting example).
    """
    try:
        logger.info(f"User {current_user.id} updating profile")
        UserPolicy.update(current_user, current_user.id)
        user = User.update(db, db_obj=current_user, obj_in=user_in)

        # Example: Invalidate cache after update
        try:
            cache().forget(f"user:{user.id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for user {user.id}", context={"error": str(e)})

        # Example: Broadcast user update event
        try:
            event = UserUpdated(user)
            broadcast().event(event)
        except Exception as e:
            logger.warning(f"Failed to broadcast user update event", context={"error": str(e)})

        logger.info(f"User {user.id} profile updated successfully")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error updating user profile",
            e,
            context={"user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Failed to update user profile")


@router.get("/", response_model=list[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve users.
    """
    UserPolicy.view_any(current_user)
    users = User.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific user (with caching example).
    """
    UserPolicy.view(current_user, user_id)

    # Example: Cache user data for 5 minutes
    cache_key = f"user:{user_id}"
    
    def get_user_data():
        user = User.get(db, id=user_id)
        if user:
            # Convert User model to UserResponse schema and serialize to JSON-compatible dict
            # Using model_dump_json() ensures datetime objects are properly serialized
            user_response = UserResponse.model_validate(user)
            return json.loads(user_response.model_dump_json())
        return None
    
    user_data = cache().remember(
        cache_key,
        ttl=300,  # 5 minutes
        callback=get_user_data,
    )

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return user_data


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a user (with cache invalidation and broadcasting example).
    """
    try:
        logger.info(f"User {current_user.id} attempting to delete user {user_id}")
        user = User.get(db, id=user_id)
       
        if not user:
            logger.warning(f"User {user_id} not found for deletion")
            raise HTTPException(status_code=404, detail="User not found")
        UserPolicy.delete(current_user, user.id)

        # Example: Invalidate cache before deletion
        try:
            cache().forget(f"user:{user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for user {user_id}", context={"error": str(e)})

        # Example: Broadcast user deletion event
        try:
            event = UserDeleted(user_id)
            broadcast().event(event)
        except Exception as e:
            logger.warning(f"Failed to broadcast user deletion event", context={"error": str(e)})

        db.delete(user)
        db.commit()
        logger.info(f"User {user_id} deleted successfully by user {current_user.id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error deleting user",
            e,
            context={"user_id": user_id, "deleted_by": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Failed to delete user")
