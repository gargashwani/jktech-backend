# 🚀 FastAPI Laravel-Style Boilerplate

[![GitHub stars](https://img.shields.io/github/stars/gargashwani/fastapi_boilerplate?style=social)](https://github.com/gargashwani/fastapi_boilerplate)
[![GitHub forks](https://img.shields.io/github/forks/gargashwani/fastapi_boilerplate?style=social)](https://github.com/gargashwani/fastapi_boilerplate/fork)
[![GitHub issues](https://img.shields.io/github/issues/gargashwani/fastapi_boilerplate)](https://github.com/gargashwani/fastapi_boilerplate/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/gargashwani/fastapi_boilerplate)](https://github.com/gargashwani/fastapi_boilerplate/pulls)
[![Documentation](https://img.shields.io/badge/docs-live-brightgreen)](https://gargashwani.github.io/fastapi_boilerplate/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://github.com/gargashwani/fastapi_boilerplate)

**The "batteries-included" developer experience of Laravel, powered by the high-performance async capabilities of FastAPI.**

This boilerplate is designed for developers who love Laravel's elegant syntax, clear structure, and powerful CLI, but want to build their next high-performance microservice or AI platform using Python.

---

## 🔥 Why This Boilerplate?

Most FastAPI projects start as a single `main.py` and grow into a chaotic mess. This project brings **opinionated structure** and **production-ready patterns** out of the box:

- 🏛️ **Domain-Driven Design**: Clear separation of Controllers, Models, Services, and Jobs.
- 🛠️ **Artisan CLI**: A powerful command-line interface for migrations, code generation, and task management.
- 📡 **Real-time Broadcasting**: Laravel-like WebSocket channels (Public/Private/Presence).
- 📦 **Unified Storage**: Fluent API for Local, S3, FTP, and SFTP.
- ⚡ **Redis Everything**: Caching (Laravel-like Cache facade) and Task Queuing (Celery) pre-configured.
- 🛡️ **Security First**: JWT auth, RBAC (Policies & Gates), Rate Limiting, and CORS protection.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (PostgreSQL & MySQL support)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Task Queue**: [Celery](https://docs.celeryq.dev/) with [Redis](https://redis.io/)
- **Testing**: [Pytest](https://docs.pytest.org/) with Coverage
- **Linting**: [Ruff](https://github.com/astral-sh/ruff) (The fastest Python linter)

---

## 🚀 Getting Started

### 🐳 Option 1: Docker (Recommended)
Launch the core stack (App, DB, Redis, Worker, Flower) with a single command:

```bash
# 1. Clone the repo
git clone https://github.com/gargashwani/fastapi_boilerplate.git && cd fastapi_boilerplate

# 2. Setup environment
cp .env.example .env

# 3. Start everything
docker compose up -d
```

#### 📊 Optional: Metrics (Prometheus & Grafana)
Metrics are optional and grouped under a Docker Compose profile. To start the metrics stack alongside the app:

```bash
docker compose --profile metrics up -d
```
The API will be available at [http://localhost:8000](http://localhost:8000), Prometheus at [http://localhost:9090](http://localhost:9090), and Grafana at [http://localhost:3000](http://localhost:3000).
1. **Setup environment & dependencies:**
   ```bash
   # Clone the repo
   git clone https://github.com/gargashwani/fastapi_boilerplate.git && cd fastapi_boilerplate

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -e .
   # or
   pip install -r requirements.txt # if generated
   ```

3. **Configure Dependencies:**
   Ensure you have **PostgreSQL** (or MySQL) and **Redis** running locally. Update your `.env` with the connection details.

4. **Run Interactive Installer:**
   ```bash
   # This handles .env creation, APP_KEY generation, and migrations
   python artisan install
   ```

5. **Start the server:**
   ```bash
   python artisan serve
   ```

### 💡 Hybrid Mode: Local App + Docker DB/Redis
If you want to run the application locally but don't want to install PostgreSQL and Redis manually, you can use Docker to provide just the infrastructure:

```bash
# Start only the database and redis
docker compose up -d db redis
```

The application (via Option 2) will now be able to connect to these services on `localhost`.

> [!TIP]
> You can disable Prometheus metrics exposure by setting `ENABLE_METRICS=false` in your `.env`.

---

## 🎮 Artisan CLI Usage

Just like Laravel, we provide an `artisan.py` script to speed up development:

```bash
# Generate a new Controller
python artisan make:controller UserProfile

# Run database migrations
python artisan migrate

# List all scheduled tasks
python artisan schedule:list

# Generate secure APP_KEY
python artisan key:generate
```

## Authentication Examples

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Test@12345",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-18T07:40:47.076834",
  "updated_at": "2025-12-18T07:40:47.076838"
}
```

**Note:** After registration, use the `/api/v1/auth/login` endpoint to get an authorization token.

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=Test@12345"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-18T07:40:47.076834",
    "updated_at": "2025-12-18T07:40:47.076838"
  }
}
```

### Using the Authorization Token

**All API endpoints (except `/api/v1/auth/login` and `/api/v1/auth/register`) require authentication.**

After login, use the `access_token` in the Authorization header for all subsequent requests:

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Without authentication, you'll receive:**
```json
{
  "detail": "Not authenticated"
}
```

**All endpoints are protected by default:**
- ✅ `/api/v1/users/*` - Requires authentication
- ✅ `/api/v1/files/*` - Requires authentication
- ✅ `/api/v1/broadcasting/*` - Requires authentication
- ❌ `/api/v1/auth/login` - Public (no authentication)
- ❌ `/api/v1/auth/register` - Public (no authentication)

### Password Requirements

- Minimum 8 characters
- Maximum 512 characters (bcrypt limitation handled automatically)
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)

## API Endpoints

### Authentication

**Public Endpoints (No authentication required):**
- `POST /api/v1/auth/register` - Register a new user (returns user info only)
- `POST /api/v1/auth/login` - Login and get access token + user info

**All other endpoints require authentication.** Include the `Authorization` header:
```
Authorization: Bearer <access_token>
```

### Users (Authentication Required)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users` - Get all users (admin only)
- `GET /api/v1/users/{user_id}` - Get specific user
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

### Files (Authentication Required)
- `POST /api/v1/files/upload` - Upload a file
- `GET /api/v1/files/download/{file_path}` - Download a file
- `GET /api/v1/files/info/{file_path}` - Get file information
- `DELETE /api/v1/files/delete/{file_path}` - Delete a file
- `GET /api/v1/files/list` - List files in directory
- `POST /api/v1/files/copy` - Copy a file
- `POST /api/v1/files/move` - Move a file

### Broadcasting (Authentication Required)
- `WS /api/v1/broadcasting/ws` - WebSocket connection endpoint (requires token in query parameter: `?token=<access_token>`)
- `POST /api/v1/broadcasting/auth` - Authorize private/presence channel access

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /metrics` - Prometheus metrics (if `ENABLE_METRICS=true`)
- `GET /` - API welcome message

## Configuration

### Database Selection

The boilerplate supports both **PostgreSQL** and **MySQL**. Switch between them by changing `DB_CONNECTION` in your `.env` file:

**PostgreSQL (Default):**
```env
DB_CONNECTION=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=fastapi_boilerplate
DB_USERNAME=postgres
DB_PASSWORD=postgres
```

**MySQL:**
```env
DB_CONNECTION=mysql+pymysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=fastapi_boilerplate
DB_USERNAME=root
DB_PASSWORD=root
# Optional: For MAMP
# DB_UNIX_SOCKET=/Applications/MAMP/tmp/mysql/mysql.sock
```

**Metrics:**
```env
ENABLE_METRICS=true # Set to false to disable Prometheus instrumentation
```

The same SQLAlchemy models work with both databases - no code changes needed!

### File Storage Configuration

The boilerplate provides a Laravel-like file storage system supporting multiple drivers:

**Local Storage (Default):**
```env
FILESYSTEM_DISK=local
FILESYSTEM_ROOT=storage/app
FILESYSTEM_URL=
```

**Amazon S3:**
```env
FILESYSTEM_DISK=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=your-bucket-name
```

**FTP:**
```env
FILESYSTEM_DISK=ftp
FTP_HOST=ftp.example.com
FTP_PORT=21
FTP_USERNAME=your-username
FTP_PASSWORD=your-password
```

**SFTP:**
```env
FILESYSTEM_DISK=sftp
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=your-username
SFTP_PASSWORD=your-password
SFTP_KEY=/path/to/private/key
```

Switch between storage drivers by changing `FILESYSTEM_DISK` - same API for all!

### Redis Configuration

Redis is used for both **caching** and **message queue**. Configure in `.env`:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Cache Configuration
CACHE_PREFIX=cache:
CACHE_DEFAULT_TTL=3600
CACHE_SERIALIZER=json
```

## Development

### Prerequisites

- Python 3.8+
- PostgreSQL or MySQL
- Redis (for caching and message queue)
- pip and virtualenv

### Running the Development Server

```bash
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Redis Setup

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Using Redis Cache

The boilerplate provides a Laravel-like caching interface:

```python
from app.core.cache import cache

# Basic operations
cache().put("key", "value", ttl=3600)
value = cache().get("key")
cache().forget("key")

# Cache-aside pattern (recommended)
user = cache().remember(
    f"user:{user_id}",
    ttl=300,
    callback=lambda: User.get(db, id=user_id)
)

# Advanced operations
cache().increment("counter")
cache().forever("key", "value")
tagged = cache().tags("users")
```

See [Redis Usage Guide](DOCS/REDIS_USAGE.md) for comprehensive examples.

### Background Tasks (Celery)

**Start Celery Worker:**
```bash
# Development (with auto-reload)
celery -A app.core.celery_app worker --loglevel=info --reload

# Production
celery -A app.core.celery_app worker --loglevel=info
```

**Monitor with Flower:**
```bash
celery -A app.core.celery_app flower
# Access at http://localhost:5555
```

**Using Tasks:**
```python
from app.jobs.tasks import send_welcome_email

# Queue a background task
send_welcome_email.delay(user.id)
```

### Task Scheduling

The boilerplate provides a Laravel-like task scheduler:

```python
from app.core.scheduler import schedule

# Define tasks in app/console/kernel.py
def schedule_tasks():
    # Run every minute
    schedule().job(cleanup_task).every_minute()
    
    # Run daily at specific time
    schedule().job(send_report).daily_at('09:00')
    
    # Run hourly
    schedule().job(process_queue).hourly()
    
    # Run weekly
    schedule().job(backup).weekly_on('sunday', '02:00')
```

**Run the scheduler:**
```bash
python artisan schedule:run
```

**List scheduled tasks:**
```bash
python artisan schedule:list
```

See [Task Scheduling Guide](DOCS/TASK_SCHEDULING.md) for comprehensive examples.

### File Storage Usage

The boilerplate provides a Laravel-like Storage facade:

```python
from app.core.storage import storage

# Store a file (private - in storage/app)
storage().put('path/to/file.txt', 'content')

# Store a public file (accessible via URL)
storage('public').put('images/logo.png', image_content)
# Accessible at: http://localhost:8000/storage/images/logo.png

# Get file content
content = storage().get('path/to/file.txt')

# Check if file exists
if storage().exists('path/to/file.txt'):
    print("File exists")

# Delete a file
storage().delete('path/to/file.txt')

# Get file URL
url = storage().url('path/to/file.txt')

# Use different disk
storage('s3').put('file.txt', 'content')
```

**Public vs Private Storage:**
- **Private** (`storage/app`): Files NOT publicly accessible - use for sensitive data
- **Public** (`public/storage`): Files publicly accessible via `/storage/` URL

See [File Storage Guide](DOCS/FILE_STORAGE.md) for comprehensive examples.

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app
```

## Documentation

- [Security Guide](DOCS/SECURITY.md) - Security best practices and features
- [Security Audit](SECURITY_AUDIT.md) - Comprehensive security audit report
- [Security Fixes](SECURITY_FIXES.md) - Summary of security improvements
- [Redis Usage Guide](DOCS/REDIS_USAGE.md) - Caching and message queue
- [Task Scheduling Guide](DOCS/TASK_SCHEDULING.md) - Scheduled task management
- [Broadcasting Guide](DOCS/BROADCASTING.md) - Real-time event broadcasting
- [HTTP Client Guide](DOCS/HTTP_CLIENT.md) - HTTP client for making requests
- [File Storage Guide](DOCS/FILE_STORAGE.md) - File storage system
- [Environment Variables](DOCS/ENVIRONMENT.md) - Complete configuration guide
- [Development Guide](DOCS/DEVELOPMENT.md) - Development workflow and best practices

## Key Features Explained

### Database Support
- **PostgreSQL & MySQL**: Switch databases via configuration - same ORM, same code
- **Alembic Migrations**: Version-controlled database schema changes
- **Connection Pooling**: Optimized database connections

### Redis Caching
- **Laravel-like API**: Familiar `cache().get()`, `cache().put()`, `cache().remember()` methods
- **Automatic Serialization**: JSON and pickle support
- **Tagged Cache**: Group related cache keys
- **TTL Support**: Automatic expiration

### Message Queue
- **Celery Integration**: Background task processing
- **Redis Backend**: Fast and reliable message broker
- **Task Monitoring**: Flower dashboard included
- **Retry Logic**: Built-in task retry support

### Task Scheduling
- **Laravel-like API**: Familiar `schedule().job()` syntax
- **Multiple Frequencies**: Every minute, hourly, daily, weekly, monthly, etc.
- **Task Types**: Commands, jobs, and shell commands
- **Advanced Features**: Timezone support, overlap prevention, conditional execution

### Real-time Broadcasting
- **Laravel-like API**: Familiar `broadcast().event()` syntax
- **Multiple Drivers**: Redis, Pusher, Ably, Log, Null
- **Channel Types**: Public, Private, Presence channels
- **WebSocket Support**: Real-time bidirectional communication
- **Channel Authorization**: Secure access control

### HTTP Client
- **Laravel-like API**: Familiar `http().get()`, `http().post()` syntax
- **Fluent Interface**: Chain methods for easy configuration
- **Authentication**: Basic auth, Bearer tokens
- **Retry Logic**: Automatic retries on failure
- **Middleware**: Custom request/response processing
- **Concurrent Requests**: Pool and batch multiple requests
- **Testing Support**: Fake responses and request recording

### File Storage
- **Laravel-like API**: Familiar `storage().put()`, `storage().get()` methods
- **Multiple Drivers**: Local, S3, FTP, SFTP support
- **Easy Switching**: Change driver via configuration
- **Unified Interface**: Same API for all storage backends

### Security
- **JWT Authentication**: Secure token-based auth with timezone-aware tokens
- **Password Hashing**: bcrypt password encryption with strength requirements
- **Authorization**: Policy and Gate-based access control
- **CORS Support**: Configurable cross-origin requests (validated in production)
- **Rate Limiting**: Built-in request throttling with Redis support
- **Security Headers**: X-Frame-Options, CSP, HSTS, and more
- **Path Traversal Protection**: Secure file operations with validation
- **File Upload Security**: Type, size, and content validation
- **Command Injection Prevention**: Secure command execution in scheduler
- **Secure Error Handling**: No information disclosure in production
- **Request ID Tracking**: Unique IDs for all requests

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 