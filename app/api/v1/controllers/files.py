"""
File Storage Endpoints
Demonstrates Laravel-like file storage usage.
"""

import io
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.file_security import (
    MAX_FILE_SIZE,
    get_file_mime_type,
    sanitize_filename,
    validate_file_extension,
    validate_file_path,
    validate_file_size,
    validate_mime_type,
)
from app.core.security import get_current_user
from app.core.storage import storage
from app.models.user import User
from config import settings

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload a file to storage with security validation.
    Similar to Laravel's file upload.
    """
    try:
        # Read file content
        content = await file.read()

        # Validate file size
        if not validate_file_size(len(content)):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB",
            )

        # Validate file extension
        if not validate_file_extension(file.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Validate MIME type
        mime_type = get_file_mime_type(content)
        if mime_type and not validate_mime_type(mime_type):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)

        # Generate unique filename
        import uuid

        file_ext = Path(safe_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        # Ensure path is within user's directory
        file_path = f"uploads/{current_user.id}/{unique_filename}"

        # Validate path
        base_dir = settings.FILESYSTEM_ROOT
        validated_path = validate_file_path(file_path, base_dir)

        # Store file using storage facade
        success = storage().put(file_path, content)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store file")

        return {
            "message": "File uploaded successfully",
            "path": file_path,
            "filename": safe_filename,
            "url": storage().url(file_path),
            "size": len(content),
        }
    except HTTPException:
        raise
    except Exception as e:
        # Don't expose internal errors in production
        error_detail = str(e) if settings.APP_DEBUG else "Upload failed"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Download a file from storage with path validation.
    """
    try:
        # Validate and sanitize file path
        base_dir = settings.FILESYSTEM_ROOT
        validated_path = validate_file_path(file_path, base_dir)

        # Ensure file exists
        if not storage().exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Get file content
        content = storage().get(file_path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")

        # Get filename from path (sanitized)
        filename = sanitize_filename(file_path.split("/")[-1])

        # Detect MIME type
        mime_type = get_file_mime_type(content) or "application/octet-stream"

        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) if settings.APP_DEBUG else "Download failed"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/info/{file_path:path}")
async def get_file_info(
    file_path: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get file information with path validation.
    """
    try:
        # Validate and sanitize file path
        base_dir = settings.FILESYSTEM_ROOT
        validated_path = validate_file_path(file_path, base_dir)

        if not storage().exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "path": file_path,
            "exists": True,
            "size": storage().size(file_path),
            "mime_type": storage().mime_type(file_path),
            "last_modified": storage().last_modified(file_path),
            "url": storage().url(file_path),
        }
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) if settings.APP_DEBUG else "Failed to get file info"
        raise HTTPException(status_code=500, detail=error_detail)


@router.delete("/delete/{file_path:path}")
async def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a file from storage with path validation.
    """
    try:
        # Validate and sanitize file path
        base_dir = settings.FILESYSTEM_ROOT
        validated_path = validate_file_path(file_path, base_dir)

        if not storage().exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        success = storage().delete(file_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")

        return {"message": "File deleted successfully", "path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) if settings.APP_DEBUG else "Delete failed"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/list")
async def list_files(
    directory: str = "",
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List files in a directory.
    """
    try:
        files = storage().files(directory)
        directories = storage().directories(directory)

        return {
            "directory": directory,
            "files": files,
            "directories": directories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.post("/copy")
async def copy_file(
    from_path: str,
    to_path: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Copy a file from one location to another.
    """
    try:
        if not storage().exists(from_path):
            raise HTTPException(status_code=404, detail="Source file not found")

        success = storage().copy(from_path, to_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to copy file")

        return {
            "message": "File copied successfully",
            "from": from_path,
            "to": to_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copy failed: {str(e)}")


@router.post("/move")
async def move_file(
    from_path: str,
    to_path: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Move a file from one location to another.
    """
    try:
        if not storage().exists(from_path):
            raise HTTPException(status_code=404, detail="Source file not found")

        success = storage().move(from_path, to_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to move file")

        return {
            "message": "File moved successfully",
            "from": from_path,
            "to": to_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move failed: {str(e)}")
