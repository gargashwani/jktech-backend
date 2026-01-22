"""
HTTP Client Usage Examples
Demonstrates various features of the Laravel-like HTTP client.
"""

from app.core.http import http


# Example 1: Basic GET request
def example_basic_get():
    """Basic GET request."""
    response = http().get("https://api.example.com/users")
    if response.successful():
        users = response.json()
        print(f"Found {len(users)} users")
    return response


# Example 2: POST with authentication
def example_post_with_auth():
    """POST request with Bearer token."""
    response = (
        http()
        .base_url("https://api.example.com")
        .with_token("your-token-here")
        .post("/posts", json={"title": "My Post", "content": "Post content"})
    )

    if response.successful():
        post = response.json()
        print(f"Created post: {post['id']}")
    return response


# Example 3: Request with retries
def example_with_retries():
    """Request with automatic retries."""
    response = http().retry(3).timeout(30.0).get("https://api.example.com/users")

    return response


# Example 4: Batch requests
def example_batch_requests():
    """Batch multiple requests."""
    requests = [
        {"method": "GET", "url": "https://api.example.com/users"},
        {"method": "GET", "url": "https://api.example.com/posts"},
        {"method": "GET", "url": "https://api.example.com/comments"},
    ]

    responses = http().batch(requests)
    results = []

    for response in responses:
        if response.successful():
            results.append(response.json())

    return results


# Example 5: Using middleware
def example_with_middleware():
    """Request with custom middleware."""

    def logging_middleware(request):
        print(f"Making request: {request.method} {request.url}")
        return request

    response = (
        http().with_middleware(logging_middleware).get("https://api.example.com/users")
    )

    return response


# Example 6: Testing with fake responses
def example_testing():
    """Testing with fake responses."""
    # Fake API responses
    http().fake(
        [
            {
                "url": "https://api.example.com/users",
                "method": "GET",
                "status": 200,
                "json": [{"id": 1, "name": "John"}],
            }
        ]
    )

    # Make request (returns fake response)
    response = http().get("https://api.example.com/users")
    assert response.successful()
    assert len(response.json()) == 1

    return response


# Example 7: Recording requests
def example_recording():
    """Record requests for inspection."""
    http().record()

    http().get("https://api.example.com/users")
    http().post("https://api.example.com/posts", json={"title": "Test"})

    # Get recorded requests
    recorded = http().recorded()
    print(f"Recorded {len(recorded)} requests")

    # Check if specific request was made
    assert http().assert_sent(lambda req: "users" in str(req.url))

    return recorded


# Example 8: API client class
class ApiClient:
    """Example API client using HTTP facade."""

    def __init__(self, base_url: str, token: str):
        self.client = http().base_url(base_url).with_token(token)

    def get_users(self):
        """Get all users."""
        return self.client.get("/users").json()

    def get_user(self, user_id: int):
        """Get specific user."""
        return self.client.get(f"/users/{user_id}").json()

    def create_user(self, data: dict):
        """Create new user."""
        return self.client.post("/users", json=data).json()

    def update_user(self, user_id: int, data: dict):
        """Update user."""
        return self.client.put(f"/users/{user_id}", json=data).json()

    def delete_user(self, user_id: int):
        """Delete user."""
        return self.client.delete(f"/users/{user_id}").ok()


# Example 9: Async requests
async def example_async():
    """Async HTTP requests."""
    # Make concurrent async requests
    users_response = await http().async_get("https://api.example.com/users")
    posts_response = await http().async_get("https://api.example.com/posts")

    users = users_response.json()
    posts = posts_response.json()

    return users, posts


# Example 10: Error handling
def example_error_handling():
    """Error handling examples."""
    response = http().get("https://api.example.com/users")

    # Check status
    if response.successful():
        return response.json()
    elif response.client_error():
        print(f"Client error: {response.status()}")
        return None
    elif response.server_error():
        print(f"Server error: {response.status()}")
        return None

    # Or throw on error
    try:
        response = http().get("https://api.example.com/users").throw()
        return response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None
