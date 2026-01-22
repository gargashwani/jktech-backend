"""
File Security Utilities
Functions for validating and securing file operations.
"""

import os
from pathlib import Path

from fastapi import HTTPException

# File upload configuration
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",  # Images
    ".pdf",
    ".doc",
    ".docx",
    ".txt",  # Documents
    ".zip",
    ".rar",  # Archives
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/zip",
    "application/x-rar-compressed",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_path(file_path: str, base_dir: str) -> str:
    """
    Validate and sanitize file path to prevent path traversal.

    Args:
        file_path: User-provided file path
        base_dir: Base directory that files must be within

    Returns:
        Validated absolute path

    Raises:
        HTTPException: If path is invalid or outside base directory
    """
    # Remove any null bytes
    file_path = file_path.replace("\x00", "")

    # Resolve path and ensure it's within base directory
    base_path = Path(base_dir).resolve()
    try:
        # Join and resolve the path
        resolved = (base_path / file_path).resolve()

        # Ensure the resolved path is within base directory
        resolved.relative_to(base_path)

        # Check for path traversal attempts
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=403, detail="Invalid file path")

        return str(resolved)
    except (ValueError, OSError):
        raise HTTPException(status_code=403, detail="Invalid file path")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Only allow alphanumeric, dots, dashes, and underscores
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in "._-":
            safe_chars.append(char)
        else:
            safe_chars.append("_")

    sanitized = "".join(safe_chars)

    # Remove leading dots (hidden files)
    sanitized = sanitized.lstrip(".")

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "file"

    return sanitized


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension is allowed.

    Args:
        filename: Filename to check

    Returns:
        True if extension is allowed
    """
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(size: int) -> bool:
    """
    Validate file size is within limits.

    Args:
        size: File size in bytes

    Returns:
        True if size is within limits
    """
    return size <= MAX_FILE_SIZE


def validate_mime_type(mime_type: str) -> bool:
    """
    Validate MIME type is allowed.

    Args:
        mime_type: MIME type to check

    Returns:
        True if MIME type is allowed
    """
    return mime_type in ALLOWED_MIME_TYPES


def get_file_mime_type(content: bytes) -> str | None:
    """
    Detect MIME type from file content.
    Uses simple magic bytes detection.

    Args:
        content: File content bytes

    Returns:
        MIME type or None
    """
    if len(content) < 4:
        return None

    # Check magic bytes
    magic_bytes = content[:4]

    # JPEG
    if magic_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"

    # PNG
    if magic_bytes == b"\x89PNG":
        return "image/png"

    # GIF
    if magic_bytes[:3] == b"GIF":
        return "image/gif"

    # PDF
    if content[:4] == b"%PDF":
        return "application/pdf"

    # ZIP
    if magic_bytes[:2] == b"PK":
        return "application/zip"

    # Try python-magic if available
    try:
        import magic

        mime = magic.from_buffer(content, mime=True)
        return mime
    except ImportError:
        pass

    return None
