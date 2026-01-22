# Logging System Documentation

## Overview

The backend now uses a Laravel-like logging system that creates log files in `storage/logs` directory with proper try-catch error handling throughout the application.

## Log File Location

All log files are stored in: `backend/storage/logs/`

## Log File Format

Log files are created with date-based naming (similar to Laravel):
- `app-2024-01-22.log` - Main application logs
- `auth-2024-01-22.log` - Authentication logs
- `books-2024-01-22.log` - Book management logs
- `documents-2024-01-22.log` - Document management logs
- `qa-2024-01-22.log` - Q&A system logs
- `http-2024-01-22.log` - HTTP request logs
- `rag-2024-01-22.log` - RAG service logs
- `openrouter-2024-01-22.log` - OpenRouter API logs
- `recommendations-2024-01-22.log` - Recommendation service logs

## Log Format

Each log entry follows this format:
```
[2024-01-22 14:30:45] app.INFO: User registered successfully | Context: {"user_id": 1, "email": "user@example.com"}
```

## Usage

### Basic Logging

```python
from app.core.logging import get_logger

logger = get_logger("app")

# Info log
logger.info("User created", context={"user_id": 1, "email": "user@example.com"})

# Error log
logger.error("Failed to process request", context={"request_id": "abc123"})

# Exception log with full traceback
try:
    # some code
    pass
except Exception as e:
    logger.exception("Error processing data", e, context={"data_id": 123})
```

### Convenience Functions

```python
from app.core.logging import log_info, log_error, log_warning, log_debug

log_info("Operation completed", context={"operation": "import"})
log_error("Operation failed", exc=exception, context={"operation": "import"})
log_warning("Deprecated feature used", context={"feature": "old_api"})
log_debug("Debug information", context={"variable": value})
```

### Using Decorator for Automatic Error Logging

```python
from app.core.logging_decorator import log_exceptions

@log_exceptions(logger_name="app", log_args=False)
async def my_function():
    # Code that might raise exceptions
    # All exceptions will be automatically logged
    pass
```

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for handled exceptions
- **CRITICAL**: Critical errors that may cause system failure

## Log Rotation

Logs are automatically rotated when they reach the maximum size:
- **Max Size**: 10MB (configurable via `LOG_MAX_SIZE`)
- **Backup Count**: 5 files (configurable via `LOG_BACKUP_COUNT`)

## Configuration

Logging can be configured in `.env`:

```env
LOG_LEVEL=INFO
LOG_FILE=storage/logs/app.log
LOG_MAX_SIZE=10485760  # 10MB in bytes
LOG_BACKUP_COUNT=5
```

## Try-Catch Handling

All controllers and services now have comprehensive try-catch blocks:

1. **Auth Controller**: Logs login attempts, registration, failures
2. **Books Controller**: Logs CRUD operations, errors
3. **Documents Controller**: Logs uploads, ingestion, errors
4. **Q&A Controller**: Logs questions, answers, errors
5. **Services**: All services log their operations and errors

## Viewing Logs

### Via Command Line

```bash
# View latest app log
tail -f storage/logs/app-$(date +%Y-%m-%d).log

# View all logs
ls -lh storage/logs/

# Search logs
grep "ERROR" storage/logs/app-*.log
```

### Via Artisan Command

```bash
python artisan.py logs:view
python artisan.py logs:clear
```

## Error Context

All error logs include relevant context:
- User IDs
- Request IDs
- File paths
- Operation details
- Error types and messages
- Full stack traces for exceptions

## Best Practices

1. **Always log exceptions** with full context
2. **Use appropriate log levels** (don't log everything as ERROR)
3. **Include context** for better debugging
4. **Don't log sensitive data** (passwords, tokens, etc.)
5. **Use structured logging** with context dictionaries

## Example Log Entries

```
[2024-01-22 14:30:45] auth.INFO: Login attempt for email: user@example.com
[2024-01-22 14:30:46] auth.INFO: Successful login for user: 1 (user@example.com)
[2024-01-22 14:31:00] books.ERROR: Error creating book | Context: {"user_id": 1, "book_data": {...}}
[2024-01-22 14:31:01] books.ERROR: Exception in create_book
Traceback (most recent call last):
  ...
```

## Log File Permissions

Make sure the `storage/logs` directory is writable:

```bash
chmod -R 775 storage/logs
```

## Production Considerations

In production:
- Set `LOG_LEVEL=WARNING` or `ERROR` to reduce log volume
- Monitor log file sizes
- Set up log rotation and cleanup
- Consider using centralized logging (ELK, CloudWatch, etc.)
- Don't expose sensitive information in logs
