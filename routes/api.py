from fastapi import APIRouter

from app.api.v1.controllers import (
    auth,
    broadcasting,
    files,
    users,
    books,
    documents,
    qa,
)


def register_api_routes() -> APIRouter:
    api_router = APIRouter()

    # Authentication routes (NO authentication required)
    # These endpoints are for getting tokens, so they must be public
    api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

    # All other routes require authentication
    # User routes (require authentication)
    api_router.include_router(users.router, prefix="/users", tags=["users"])

    # File routes (require authentication)
    api_router.include_router(files.router, prefix="/files", tags=["files"])

    # Broadcasting routes (require authentication)
    api_router.include_router(
        broadcasting.router, prefix="/broadcasting", tags=["broadcasting"]
    )

    # Book management routes (require authentication)
    api_router.include_router(books.router, tags=["books"])

    # Document management routes (require authentication)
    api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

    # Q&A routes (require authentication)
    api_router.include_router(qa.router, prefix="/qa", tags=["qa"])

    return api_router
