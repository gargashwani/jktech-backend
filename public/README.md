# Public Directory

This directory contains publicly accessible files, similar to Laravel's `public` directory.

## Directory Structure

```
public/
├── storage/      # Publicly accessible storage files
├── css/          # CSS files
├── js/           # JavaScript files
└── images/       # Image files
```

## Accessing Files

Files in this directory are served directly via HTTP:

- **Public files**: `http://localhost:8000/public/{path}`
- **Storage files**: `http://localhost:8000/storage/{path}`

## Usage

### Storing Public Files

Use the `public` disk to store files that should be publicly accessible:

```python
from app.core.storage import storage

# Store file in public storage
storage('public').put('uploads/image.jpg', image_content)

# File will be accessible at: http://localhost:8000/storage/uploads/image.jpg
```

### Private vs Public Storage

- **Private Storage** (`storage/app`): Files stored here are NOT publicly accessible
  - Use for sensitive files, user uploads that need authentication, etc.
  - Access via API endpoints only

- **Public Storage** (`public/storage`): Files stored here ARE publicly accessible
  - Use for images, CSS, JS, public assets
  - Accessible directly via URL without authentication

## Example

```python
# Store private file (requires authentication to access)
storage('local').put('private/document.pdf', content)

# Store public file (accessible via URL)
storage('public').put('images/logo.png', image_content)
# Accessible at: http://localhost:8000/storage/images/logo.png
```

