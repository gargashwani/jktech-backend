from fastapi import APIRouter

from app.api.v1.controllers import auth, broadcasting, files, users, books, documents, qa

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(
    broadcasting.router, prefix="/broadcasting", tags=["broadcasting"]
)
api_router.include_router(books.router, tags=["books"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])