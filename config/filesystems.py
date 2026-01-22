"""
Filesystem Configuration
Similar to Laravel's config/filesystems.php
"""

import os

filesystems_config = {
    "disk": os.getenv("FILESYSTEM_DISK", "local"),
    "root": os.getenv("FILESYSTEM_ROOT", "storage/app"),
    "public_root": os.getenv("FILESYSTEM_PUBLIC_ROOT", "public/storage"),
    "url": os.getenv("FILESYSTEM_URL"),
    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "aws_default_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    "aws_bucket": os.getenv("AWS_BUCKET"),
    "aws_endpoint": os.getenv("AWS_ENDPOINT"),
    "ftp_host": os.getenv("FTP_HOST", "localhost"),
    "ftp_port": int(os.getenv("FTP_PORT", "21")),
    "ftp_username": os.getenv("FTP_USERNAME"),
    "ftp_password": os.getenv("FTP_PASSWORD"),
    "sftp_host": os.getenv("SFTP_HOST", "localhost"),
    "sftp_port": int(os.getenv("SFTP_PORT", "22")),
    "sftp_username": os.getenv("SFTP_USERNAME"),
    "sftp_password": os.getenv("SFTP_PASSWORD"),
    "sftp_key": os.getenv("SFTP_KEY"),
}
