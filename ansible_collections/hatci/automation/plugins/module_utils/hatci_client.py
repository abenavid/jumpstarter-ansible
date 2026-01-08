#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Shared HTTP client for HATCI API modules.

This module provides a common interface for making authenticated HTTP requests
to the HATCI SUMS API backend.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class HATCIClientError(Exception):
    """Base exception for HATCI client errors."""

    pass


class HATCIClient:
    """
    HTTP client for HATCI SUMS API.

    Handles authentication, request formatting, error handling, and response parsing.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        verify_tls: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize HATCI client.

        Args:
            base_url: Base URL for HATCI API (e.g., https://api.hatci.example.com)
            token: Authentication token for API requests
            verify_tls: Whether to verify TLS certificates (default: True)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_tls = verify_tls
        self.timeout = timeout

    def _build_url(self, path: str) -> str:
        """Build full URL from API path."""
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _build_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Build HTTP headers with authentication."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }
        return headers

    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to HATCI API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API endpoint path
            data: Request body data (will be JSON encoded)
            params: Query parameters

        Returns:
            Parsed JSON response as dictionary

        Raises:
            HATCIClientError: On HTTP errors or invalid responses
        """
        url = self._build_url(path)

        # Add query parameters if provided
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        # Prepare request
        headers = self._build_headers()
        request_data = None

        if data and method in ("POST", "PUT", "PATCH"):
            request_data = json.dumps(data).encode("utf-8")

        # Create request
        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        # SSL context for TLS verification
        ssl_context = None
        if not self.verify_tls:
            import ssl

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        try:
            # Make request
            with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
                response_body = response.read().decode("utf-8")
                status_code = response.getcode()

                # Parse JSON response
                try:
                    result = json.loads(response_body) if response_body else {}
                except json.JSONDecodeError as e:
                    raise HATCIClientError(
                        f"Invalid JSON response from API (status {status_code}): {e}"
                    ) from e

                # Check for HTTP errors
                if status_code >= 400:
                    error_msg = result.get("error", result.get("message", "Unknown error"))
                    raise HATCIClientError(
                        f"API request failed (status {status_code}): {error_msg}"
                    )

                return result

        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body) if error_body else {}
                error_msg = error_data.get("error", error_data.get("message", e.reason))
            except json.JSONDecodeError:
                error_msg = error_body or e.reason

            raise HATCIClientError(f"HTTP {e.code}: {error_msg}") from e

        except urllib.error.URLError as e:
            raise HATCIClientError(f"Network error: {e.reason}") from e

        except Exception as e:
            raise HATCIClientError(f"Unexpected error: {str(e)}") from e

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", path, params=params)

    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", path, data=data)

    def put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request("PUT", path, data=data)

    def patch(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PATCH request."""
        return self._make_request("PATCH", path, data=data)

    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request("DELETE", path)
