"""
File Storage Utility
Provides Laravel-like Storage facade using PyFilesystem2.
Supports local filesystem, S3, FTP, SFTP, and more.
"""

import logging
import os
from typing import BinaryIO

from config import settings

logger = logging.getLogger(__name__)


# Lazy import helper - avoids import errors during migrations
def _ensure_fs_imported():
    """Ensure fs modules are imported, raise error if not available."""
    global open_fs, FS
    if open_fs is None:
        try:
            from fs import open_fs as _open_fs
            from fs.base import FS as _FS

            open_fs = _open_fs
            FS = _FS
        except ImportError:
            raise ImportError(
                "PyFilesystem2 (fs) is required for file storage. "
                "Install with: pip install fs fs-s3fs boto3"
            )
    return open_fs, FS


# Initialize as None - will be imported lazily when Storage is actually used
open_fs = None
FS = None


class Storage:
    """
    Laravel-like Storage facade for file operations.
    Supports multiple storage drivers: local, s3, ftp, sftp, etc.
    """

    def __init__(self, disk: str | None = None):
        """
        Initialize storage with specified disk.

        Args:
            disk: Storage disk name (defaults to FILESYSTEM_DISK from config)
        """
        self.disk = disk or settings.FILESYSTEM_DISK
        self._filesystem: FS | None = None

    @property
    def filesystem(self) -> FS:
        """Get or create filesystem instance."""
        if self._filesystem is None:
            self._filesystem = self._create_filesystem()
        return self._filesystem

    def _create_filesystem(self) -> FS:
        """Create filesystem instance based on disk configuration."""
        # Ensure fs modules are imported
        _open_fs, _FS = _ensure_fs_imported()

        # Get disk configuration from settings
        disk_config = self._get_disk_config()
        driver = disk_config.get("driver", "local")

        if driver == "local":
            root = disk_config.get("root", settings.FILESYSTEM_ROOT)
            # Create directory if it doesn't exist
            os.makedirs(root, exist_ok=True)
            return _open_fs(f"osfs://{os.path.abspath(root)}")

        elif driver == "s3":
            return self._create_s3_filesystem(disk_config)

        elif driver == "ftp":
            return self._create_ftp_filesystem(disk_config)

        elif driver == "sftp":
            return self._create_sftp_filesystem(disk_config)

        else:
            raise ValueError(f"Unsupported storage driver: {driver}")

    def _get_disk_config(self) -> dict:
        """Get disk configuration from settings."""
        if self.disk == "local":
            return {
                "driver": "local",
                "root": settings.FILESYSTEM_ROOT,
            }
        elif self.disk == "public":
            # Public storage disk - files stored in public/storage
            return {
                "driver": "local",
                "root": settings.FILESYSTEM_PUBLIC_ROOT,
            }
        elif self.disk == "s3":
            return {
                "driver": "s3",
                "key": getattr(settings, "AWS_ACCESS_KEY_ID", None),
                "secret": getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
                "region": getattr(settings, "AWS_DEFAULT_REGION", "us-east-1"),
                "bucket": getattr(settings, "AWS_BUCKET", None),
                "endpoint": getattr(settings, "AWS_ENDPOINT", None),
            }
        elif self.disk == "ftp":
            return {
                "driver": "ftp",
                "host": getattr(settings, "FTP_HOST", "localhost"),
                "port": getattr(settings, "FTP_PORT", 21),
                "username": getattr(settings, "FTP_USERNAME", None),
                "password": getattr(settings, "FTP_PASSWORD", None),
            }
        elif self.disk == "sftp":
            return {
                "driver": "sftp",
                "host": getattr(settings, "SFTP_HOST", "localhost"),
                "port": getattr(settings, "SFTP_PORT", 22),
                "username": getattr(settings, "SFTP_USERNAME", None),
                "password": getattr(settings, "SFTP_PASSWORD", None),
                "key": getattr(settings, "SFTP_KEY", None),
            }
        else:
            # Default to local
            return {
                "driver": "local",
                "root": settings.FILESYSTEM_ROOT,
            }

    def _create_s3_filesystem(self, config: dict) -> FS:
        """Create S3 filesystem."""
        try:
            from fs_s3fs import S3FS

            bucket = config.get("bucket")
            region = config.get("region", "us-east-1")
            access_key_id = config.get("key")
            secret_access_key = config.get("secret")
            endpoint_url = config.get("endpoint")

            if not bucket:
                raise ValueError("S3 bucket name is required")

            return S3FS(
                bucket_name=bucket,
                region=region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                endpoint_url=endpoint_url,
            )
        except ImportError:
            raise ImportError(
                "fs-s3fs is required for S3 storage. Install it with: pip install fs-s3fs"
            )

    def _create_ftp_filesystem(self, config: dict) -> FS:
        """Create FTP filesystem."""
        try:
            from fs.ftpfs import FTPFS

            host = config.get("host", "localhost")
            port = config.get("port", 21)
            user = config.get("username")
            password = config.get("password")

            return FTPFS(host, port=port, user=user, passwd=password)
        except ImportError:
            raise ImportError("FTP support requires fs.ftpfs")

    def _create_sftp_filesystem(self, config: dict) -> FS:
        """Create SFTP filesystem."""
        try:
            from fs.sshfs import SSHFS

            host = config.get("host", "localhost")
            port = config.get("port", 22)
            user = config.get("username")
            password = config.get("password")
            key_file = config.get("key")

            return SSHFS(
                host,
                port=port,
                user=user,
                passwd=password,
                pkey_path=key_file,
            )
        except ImportError:
            raise ImportError("SFTP support requires fs.sshfs")

    def put(
        self, path: str, content: str | bytes | BinaryIO, overwrite: bool = True
    ) -> bool:
        """
        Store file content at given path.
        Similar to Laravel's Storage::put().

        Args:
            path: File path
            content: File content (string, bytes, or file-like object)
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful
        """
        try:
            if not overwrite and self.exists(path):
                return False

            # Handle different content types
            if isinstance(content, str):
                content = content.encode("utf-8")
            elif hasattr(content, "read"):
                content = content.read()

            # Ensure directory exists
            dir_path = os.path.dirname(path)
            if dir_path:
                self.filesystem.makedirs(dir_path, recreate=True)

            with self.filesystem.open(path, "wb") as f:
                if isinstance(content, bytes):
                    f.write(content)
                else:
                    f.write(content.encode("utf-8"))

            return True
        except Exception as e:
            logger.error(f"Storage put error for {path}: {e}")
            return False

    def get(self, path: str) -> bytes | None:
        """
        Get file content.
        Similar to Laravel's Storage::get().

        Args:
            path: File path

        Returns:
            File content as bytes, or None if not found
        """
        try:
            if not self.exists(path):
                return None

            with self.filesystem.open(path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Storage get error for {path}: {e}")
            return None

    def exists(self, path: str) -> bool:
        """
        Check if file exists.
        Similar to Laravel's Storage::exists().

        Args:
            path: File path

        Returns:
            True if file exists
        """
        try:
            return self.filesystem.exists(path) and self.filesystem.isfile(path)
        except Exception:
            return False

    def delete(self, path: str) -> bool:
        """
        Delete file.
        Similar to Laravel's Storage::delete().

        Args:
            path: File path

        Returns:
            True if deleted successfully
        """
        try:
            if not self.exists(path):
                return False

            self.filesystem.remove(path)
            return True
        except Exception as e:
            logger.error(f"Storage delete error for {path}: {e}")
            return False

    def copy(self, from_path: str, to_path: str) -> bool:
        """
        Copy file from one location to another.
        Similar to Laravel's Storage::copy().

        Args:
            from_path: Source path
            to_path: Destination path

        Returns:
            True if copied successfully
        """
        try:
            if not self.exists(from_path):
                return False

            # Ensure destination directory exists
            dir_path = os.path.dirname(to_path)
            if dir_path:
                self.filesystem.makedirs(dir_path, recreate=True)

            self.filesystem.copy(from_path, to_path, overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Storage copy error from {from_path} to {to_path}: {e}")
            return False

    def move(self, from_path: str, to_path: str) -> bool:
        """
        Move file from one location to another.
        Similar to Laravel's Storage::move().

        Args:
            from_path: Source path
            to_path: Destination path

        Returns:
            True if moved successfully
        """
        try:
            if not self.exists(from_path):
                return False

            # Ensure destination directory exists
            dir_path = os.path.dirname(to_path)
            if dir_path:
                self.filesystem.makedirs(dir_path, recreate=True)

            self.filesystem.move(from_path, to_path, overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Storage move error from {from_path} to {to_path}: {e}")
            return False

    def size(self, path: str) -> int | None:
        """
        Get file size in bytes.
        Similar to Laravel's Storage::size().

        Args:
            path: File path

        Returns:
            File size in bytes, or None if not found
        """
        try:
            if not self.exists(path):
                return None
            return self.filesystem.getsize(path)
        except Exception:
            return None

    def mime_type(self, path: str) -> str | None:
        """
        Get file MIME type.
        Similar to Laravel's Storage::mimeType().

        Args:
            path: File path

        Returns:
            MIME type, or None if not found
        """
        try:
            if not self.exists(path):
                return None
            return self.filesystem.getmimetype(path)
        except Exception:
            return None

    def last_modified(self, path: str) -> float | None:
        """
        Get file last modified timestamp.
        Similar to Laravel's Storage::lastModified().

        Args:
            path: File path

        Returns:
            Unix timestamp, or None if not found
        """
        try:
            if not self.exists(path):
                return None
            info = self.filesystem.getinfo(path, namespaces=["details"])
            return info.modified.timestamp() if info.modified else None
        except Exception:
            return None

    def files(self, directory: str = "") -> list[str]:
        """
        Get list of files in directory.
        Similar to Laravel's Storage::files().

        Args:
            directory: Directory path

        Returns:
            List of file paths
        """
        try:
            files = []
            for path in self.filesystem.walk.files(directory):
                files.append(path)
            return files
        except Exception as e:
            logger.error(f"Storage files error for {directory}: {e}")
            return []

    def directories(self, directory: str = "") -> list[str]:
        """
        Get list of directories.
        Similar to Laravel's Storage::directories().

        Args:
            directory: Directory path

        Returns:
            List of directory paths
        """
        try:
            dirs = []
            for path in self.filesystem.walk.dirs(directory):
                dirs.append(path)
            return dirs
        except Exception as e:
            logger.error(f"Storage directories error for {directory}: {e}")
            return []

    def make_directory(self, path: str) -> bool:
        """
        Create directory.
        Similar to Laravel's Storage::makeDirectory().

        Args:
            path: Directory path

        Returns:
            True if created successfully
        """
        try:
            self.filesystem.makedirs(path, recreate=True)
            return True
        except Exception as e:
            logger.error(f"Storage makeDirectory error for {path}: {e}")
            return False

    def delete_directory(self, path: str) -> bool:
        """
        Delete directory.
        Similar to Laravel's Storage::deleteDirectory().

        Args:
            path: Directory path

        Returns:
            True if deleted successfully
        """
        try:
            if not self.filesystem.exists(path):
                return False

            self.filesystem.removetree(path)
            return True
        except Exception as e:
            logger.error(f"Storage deleteDirectory error for {path}: {e}")
            return False

    def url(self, path: str) -> str | None:
        """
        Get URL for file.
        Similar to Laravel's Storage::url().

        Args:
            path: File path

        Returns:
            File URL, or None if not available
        """
        try:
            # For local filesystem, return relative URL
            if self.disk == "local" or settings.FILESYSTEM_DISK == "local":
                base_url = settings.FILESYSTEM_URL or settings.APP_URL
                # Remove trailing slash if present
                base_url = base_url.rstrip("/")
                return f"{base_url}/storage/{path}"

            # For public disk, return public URL
            elif self.disk == "public":
                base_url = settings.FILESYSTEM_URL or settings.APP_URL
                base_url = base_url.rstrip("/")
                return f"{base_url}/storage/{path}"

            # For S3, return S3 URL
            elif self.disk == "s3" or settings.FILESYSTEM_DISK == "s3":
                disk_config = self._get_disk_config()
                bucket = disk_config.get("bucket")
                region = disk_config.get("region", "us-east-1")
                if bucket:
                    return f"https://{bucket}.s3.{region}.amazonaws.com/{path}"

            # For other filesystems, return None
            return None
        except Exception as e:
            logger.error(f"Storage url error for {path}: {e}")
            return None

    def use_disk(self, name: str) -> "Storage":
        """
        Get storage instance for different disk.
        Similar to Laravel's Storage::disk().

        Args:
            name: Disk name

        Returns:
            New Storage instance
        """
        return Storage(disk=name)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._filesystem:
            self._filesystem.close()
            self._filesystem = None


# Global storage instance
_storage_instance: Storage | None = None


def get_storage(disk: str | None = None) -> Storage:
    """Get global storage instance (singleton)."""
    global _storage_instance
    if _storage_instance is None or disk:
        _storage_instance = Storage(disk=disk)
    return _storage_instance


# Convenience function (Laravel-like API)
def storage(disk: str | None = None) -> Storage:
    """
    Get storage instance - Laravel-like API.

    Usage:
        storage().put('file.txt', 'content')
        storage('s3').put('file.txt', 'content')
    """
    return get_storage(disk)
