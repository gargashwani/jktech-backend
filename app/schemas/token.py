from pydantic import BaseModel

from app.schemas.user import UserResponse


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithUser(BaseModel):
    """Token response with user information"""

    access_token: str
    token_type: str
    user: UserResponse


class TokenPayload(BaseModel):
    sub: int = None
