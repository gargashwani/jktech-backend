"""
HTTP Client Facade
Laravel-like HTTP client using httpx.
Supports making requests, middleware, retries, concurrent requests, and testing.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import httpx
from httpx import Request, Response, Timeout

logger = logging.getLogger(__name__)


class Http:
    """
    HTTP Client Facade similar to Laravel's Http facade.
    Provides a fluent interface for making HTTP requests.
    """

    def __init__(self):
        self._base_url: str | None = None
        self._headers: dict[str, str] = {}
        self._timeout: float | None = None
        self._retries: int = 0
        self._middleware: list[Callable] = []
        self._options: dict[str, Any] = {}
        self._auth: tuple | None = None
        self._bearer_token: str | None = None
        self._verify: bool = True
        self._follow_redirects: bool = True
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None
        self._fake_responses: list[dict[str, Any]] = []
        self._fake_enabled: bool = False
        self._recorded_requests: list[Request] = []
        self._prevent_stray_requests: bool = False

    def base_url(self, url: str) -> "Http":
        """Set base URL for all requests."""
        self._base_url = url
        return self

    def with_headers(self, headers: dict[str, str]) -> "Http":
        """Set headers for requests."""
        self._headers.update(headers)
        return self

    def with_header(self, key: str, value: str) -> "Http":
        """Set a single header."""
        self._headers[key] = value
        return self

    def with_basic_auth(self, username: str, password: str) -> "Http":
        """Set basic authentication."""
        self._auth = (username, password)
        return self

    def with_token(self, token: str) -> "Http":
        """Set bearer token authentication."""
        self._bearer_token = token
        self._headers["Authorization"] = f"Bearer {token}"
        return self

    def with_options(self, **options) -> "Http":
        """Set httpx client options."""
        self._options.update(options)
        return self

    def timeout(self, seconds: float) -> "Http":
        """Set request timeout."""
        self._timeout = seconds
        return self

    def retry(self, times: int = 3, retry_on: list[int] | None = None) -> "Http":
        """
        Set retry attempts.

        Args:
            times: Number of retry attempts
            retry_on: List of HTTP status codes to retry on (default: [500, 502, 503, 504])
        """
        self._retries = times
        self._retry_on = retry_on or [500, 502, 503, 504]
        return self

    def without_verifying(self) -> "Http":
        """Disable SSL verification."""
        self._verify = False
        return self

    def without_redirecting(self) -> "Http":
        """Disable following redirects."""
        self._follow_redirects = False
        return self

    def with_middleware(self, middleware: Callable) -> "Http":
        """Add middleware to request pipeline."""
        self._middleware.append(middleware)
        return self

    def _build_url(self, url: str) -> str:
        """Build full URL from base URL and path."""
        if self._base_url:
            if url.startswith("http"):
                return url
            base = self._base_url.rstrip("/")
            path = url.lstrip("/")
            return f"{base}/{path}"
        return url

    def _build_headers(
        self, additional_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Build headers with authentication."""
        headers = self._headers.copy()
        if additional_headers:
            headers.update(additional_headers)
        if self._bearer_token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        return headers

    def _build_timeout(self) -> Timeout | None:
        """Build timeout configuration."""
        if self._timeout:
            return Timeout(self._timeout)
        return None

    def _get_client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                verify=self._verify,
                follow_redirects=self._follow_redirects,
                timeout=self._build_timeout(),
                **self._options,
            )
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                verify=self._verify,
                follow_redirects=self._follow_redirects,
                timeout=self._build_timeout(),
                **self._options,
            )
        return self._async_client

    def _apply_middleware(self, request: Request) -> Request:
        """Apply middleware to request."""
        for middleware in self._middleware:
            request = middleware(request)
        return request

    def _should_retry(
        self, response: Response | None, exception: Exception | None = None
    ) -> bool:
        """Check if request should be retried."""
        if self._retries <= 0:
            return False
        if exception:
            return True
        if response and response.status_code in getattr(
            self, "_retry_on", [500, 502, 503, 504]
        ):
            return True
        return False

    def _make_request(
        self,
        method: str,
        url: str,
        data: Any | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        files: dict | None = None,
    ) -> Response:
        """Make HTTP request with retry logic."""
        full_url = self._build_url(url)
        request_headers = self._build_headers(headers)

        # Check for fake responses
        if self._fake_enabled:
            return self._get_fake_response(method, full_url)

        # Record request if recording
        if hasattr(self, "_record_requests") and self._record_requests:
            self._recorded_requests.append(
                Request(method, full_url, headers=request_headers)
            )

        client = self._get_client()
        attempts = 0
        last_exception = None

        while attempts <= self._retries:
            try:
                # Apply middleware
                request = Request(method, full_url, headers=request_headers)
                request = self._apply_middleware(request)

                # Make request
                response = client.request(
                    method=method,
                    url=full_url,
                    content=data,
                    json=json,
                    params=params,
                    headers=request_headers,
                    files=files,
                    auth=self._auth,
                )

                # Check if retry needed
                if not self._should_retry(response):
                    return response

                attempts += 1
                if attempts <= self._retries:
                    logger.warning(
                        f"Request failed, retrying ({attempts}/{self._retries}): {full_url}"
                    )
                    continue

                return response

            except Exception as e:
                last_exception = e
                attempts += 1
                if attempts <= self._retries:
                    logger.warning(
                        f"Request exception, retrying ({attempts}/{self._retries}): {e}"
                    )
                    continue
                raise

        if last_exception:
            raise last_exception

        raise Exception("Request failed after retries")

    async def _make_async_request(
        self,
        method: str,
        url: str,
        data: Any | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        files: dict | None = None,
    ) -> Response:
        """Make async HTTP request with retry logic."""
        full_url = self._build_url(url)
        request_headers = self._build_headers(headers)

        # Check for fake responses
        if self._fake_enabled:
            return self._get_fake_response(method, full_url)

        client = self._get_async_client()
        attempts = 0
        last_exception = None

        while attempts <= self._retries:
            try:
                response = await client.request(
                    method=method,
                    url=full_url,
                    content=data,
                    json=json,
                    params=params,
                    headers=request_headers,
                    files=files,
                    auth=self._auth,
                )

                if not self._should_retry(response):
                    return response

                attempts += 1
                if attempts <= self._retries:
                    logger.warning(
                        f"Request failed, retrying ({attempts}/{self._retries}): {full_url}"
                    )
                    continue

                return response

            except Exception as e:
                last_exception = e
                attempts += 1
                if attempts <= self._retries:
                    logger.warning(
                        f"Request exception, retrying ({attempts}/{self._retries}): {e}"
                    )
                    continue
                raise

        if last_exception:
            raise last_exception

        raise Exception("Request failed after retries")

    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make GET request."""
        return HttpResponse(self._make_request("GET", url, **kwargs))

    def post(self, url: str, **kwargs) -> HttpResponse:
        """Make POST request."""
        return HttpResponse(self._make_request("POST", url, **kwargs))

    def put(self, url: str, **kwargs) -> HttpResponse:
        """Make PUT request."""
        return HttpResponse(self._make_request("PUT", url, **kwargs))

    def patch(self, url: str, **kwargs) -> HttpResponse:
        """Make PATCH request."""
        return HttpResponse(self._make_request("PATCH", url, **kwargs))

    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make DELETE request."""
        return HttpResponse(self._make_request("DELETE", url, **kwargs))

    async def async_get(self, url: str, **kwargs) -> HttpResponse:
        """Make async GET request."""
        return HttpResponse(await self._make_async_request("GET", url, **kwargs))

    async def async_post(self, url: str, **kwargs) -> HttpResponse:
        """Make async POST request."""
        return HttpResponse(await self._make_async_request("POST", url, **kwargs))

    async def async_put(self, url: str, **kwargs) -> HttpResponse:
        """Make async PUT request."""
        return HttpResponse(await self._make_async_request("PUT", url, **kwargs))

    async def async_patch(self, url: str, **kwargs) -> HttpResponse:
        """Make async PATCH request."""
        return HttpResponse(await self._make_async_request("PATCH", url, **kwargs))

    async def async_delete(self, url: str, **kwargs) -> HttpResponse:
        """Make async DELETE request."""
        return HttpResponse(await self._make_async_request("DELETE", url, **kwargs))

    def pool(self, requests: list[Callable]) -> list[HttpResponse]:
        """
        Execute multiple requests concurrently using a connection pool.

        Args:
            requests: List of callable functions that return Response objects

        Returns:
            List of HttpResponse objects
        """
        # For synchronous pool, use threading
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(req) for req in requests]
            return [
                HttpResponse(future.result())
                for future in concurrent.futures.as_completed(futures)
            ]

    async def async_pool(self, requests: list[Callable]) -> list[HttpResponse]:
        """
        Execute multiple async requests concurrently.

        Args:
            requests: List of async callable functions that return Response objects

        Returns:
            List of HttpResponse objects
        """
        responses = await asyncio.gather(*[req() for req in requests])
        return [HttpResponse(r) for r in responses]

    def batch(self, requests: list[dict[str, Any]]) -> list[HttpResponse]:
        """
        Batch multiple requests.

        Args:
            requests: List of request dictionaries with 'method', 'url', and optional 'data', 'json', etc.

        Returns:
            List of HttpResponse objects
        """

        def make_req(req: dict[str, Any]) -> Response:
            req_copy = req.copy()
            method = req_copy.pop("method")
            url = req_copy.pop("url")
            return self._make_request(method, url, **req_copy)

        return self.pool([lambda r=r: make_req(r) for r in requests])

    async def async_batch(self, requests: list[dict[str, Any]]) -> list[HttpResponse]:
        """
        Batch multiple async requests.

        Args:
            requests: List of request dictionaries

        Returns:
            List of HttpResponse objects
        """

        async def make_req(req: dict[str, Any]) -> Response:
            req_copy = req.copy()
            method = req_copy.pop("method")
            url = req_copy.pop("url")
            return await self._make_async_request(method, url, **req_copy)

        responses = await asyncio.gather(*[make_req(r) for r in requests])
        return [HttpResponse(r) for r in responses]

    # Testing methods
    def fake(self, responses: list[dict[str, Any]]) -> "Http":
        """
        Fake responses for testing.

        Args:
            responses: List of response dictionaries with 'url', 'method', 'status', 'json', 'text', etc.
        """
        self._fake_enabled = True
        self._fake_responses = responses
        return self

    def _get_fake_response(self, method: str, url: str) -> Response:
        """Get fake response for testing."""
        for fake in self._fake_responses:
            fake_method = fake.get("method", "GET").upper()
            fake_url = fake.get("url", "")

            if fake_method == method.upper() and (fake_url == url or fake_url in url):
                status_code = fake.get("status", 200)
                json_data = fake.get("json")
                text = fake.get("text", "")
                headers = fake.get("headers", {})

                # Create mock response
                response = Response(
                    status_code=status_code,
                    headers=headers,
                    content=json.dumps(json_data).encode()
                    if json_data
                    else text.encode(),
                )
                return response

        if self._prevent_stray_requests:
            raise Exception(f"Unexpected request: {method} {url}")

        # Return default fake response
        return Response(status_code=200, content=b"{}")

    def record(self) -> "Http":
        """Start recording requests."""
        self._record_requests = True
        self._recorded_requests = []
        return self

    def recorded(self) -> list[Request]:
        """Get recorded requests."""
        return self._recorded_requests

    def assert_sent(self, callback: Callable | None = None) -> bool:
        """
        Assert that requests were sent.

        Args:
            callback: Optional callback to check requests

        Returns:
            True if assertion passes
        """
        if callback:
            return any(callback(req) for req in self._recorded_requests)
        return len(self._recorded_requests) > 0

    def prevent_stray_requests(self) -> "Http":
        """Prevent unexpected requests during testing."""
        self._prevent_stray_requests = True
        return self

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        if self._client:
            self._client.close()
        if self._async_client:
            # Note: async client should be closed with await
            pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup."""
        if self._async_client:
            await self._async_client.aclose()


class HttpResponse:
    """
    Response wrapper with helper methods.
    Similar to Laravel's response helpers.
    """

    def __init__(self, response: Response):
        self.response = response

    def json(self) -> Any:
        """Get JSON response data."""
        return self.response.json()

    def text(self) -> str:
        """Get text response."""
        return self.response.text

    def body(self) -> bytes:
        """Get raw response body."""
        return self.response.content

    def status(self) -> int:
        """Get status code."""
        return self.response.status_code

    def successful(self) -> bool:
        """Check if request was successful (2xx)."""
        return 200 <= self.response.status_code < 300

    def ok(self) -> bool:
        """Check if status is 200."""
        return self.response.status_code == 200

    def failed(self) -> bool:
        """Check if request failed (4xx or 5xx)."""
        return self.response.status_code >= 400

    def client_error(self) -> bool:
        """Check if client error (4xx)."""
        return 400 <= self.response.status_code < 500

    def server_error(self) -> bool:
        """Check if server error (5xx)."""
        return 500 <= self.response.status_code < 600

    def headers(self) -> dict[str, str]:
        """Get response headers."""
        return dict(self.response.headers)

    def header(self, key: str, default: str | None = None) -> str | None:
        """Get specific header."""
        return self.response.headers.get(key, default)

    def on_error(self, callback: Callable[[Response], None]) -> "HttpResponse":
        """Execute callback on error."""
        if self.failed():
            callback(self.response)
        return self

    def throw(self) -> "HttpResponse":
        """Throw exception if request failed."""
        if self.failed():
            raise Exception(f"HTTP {self.status()}: {self.text()}")
        return self

    def __getattr__(self, name: str):
        """Delegate to underlying response."""
        return getattr(self.response, name)


# Global HTTP instance
_http_instance: Http | None = None


def get_http() -> Http:
    """Get global HTTP instance."""
    global _http_instance
    if _http_instance is None:
        _http_instance = Http()
    return _http_instance


def http() -> Http:
    """
    Get HTTP client - Laravel-like API.

    Usage:
        http().get('https://api.example.com/users')
        http().with_token(token).post('https://api.example.com/posts', json=data)
    """
    return get_http()


# Macro support
_http_macros: dict[str, Callable] = {}


def macro(name: str, callback: Callable):
    """Register an HTTP macro."""
    _http_macros[name] = callback


def __getattr__(name: str):
    """Support for macros."""
    if name in _http_macros:
        return _http_macros[name]
    raise AttributeError(f"'{Http.__name__}' object has no attribute '{name}'")
