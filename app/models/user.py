from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import Base
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def get(cls, db: Session, id: int) -> Optional["User"]:
        return db.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        return db.query(cls).filter(cls.email == email).first()

    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional["User"]:
        user = cls.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create(cls, db: Session, obj_in: UserCreate) -> "User":
        db_obj = cls(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @classmethod
    def update(cls, db: Session, db_obj: "User", obj_in: UserUpdate) -> "User":
        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @classmethod
    def get_multi(cls, db: Session, skip: int = 0, limit: int = 100) -> list["User"]:
        return db.query(cls).offset(skip).limit(limit).all()

    # Async methods
    @classmethod
    async def get_async(cls, db: AsyncSession, id: int) -> Optional["User"]:
        """Get a user by ID (async)."""
        result = await db.execute(select(cls).filter(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email_async(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get a user by email (async)."""
        result = await db.execute(select(cls).filter(cls.email == email))
        return result.scalar_one_or_none()
