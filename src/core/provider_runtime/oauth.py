from __future__ import annotations

import base64
import hashlib
import secrets
import socket
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event
from typing import Mapping
from urllib.parse import parse_qs, urlsplit, urlunsplit


class BrowserOAuthError(ValueError):
    """Raised when an OAuth browser session cannot be started or completed safely."""


@dataclass(frozen=True, slots=True)
class BrowserOAuthSession:
    provider_id: str
    authorization_url: str
    redirect_uri: str
    state: str
    code_verifier: str
    code_challenge: str
    callback_mode: str
    timeout_seconds: int


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_verifier() -> str:
    # RFC 7636 requires 43-128 characters from the unreserved URI set.
    verifier = secrets.token_urlsafe(64).rstrip("=")
    if len(verifier) < 43:
        verifier += secrets.token_urlsafe(16).rstrip("=")
    return verifier[:128]


def pkce_s256_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _normalized_callback_identity(uri: str) -> tuple[str, str, int | None, str]:
    parsed = urlsplit(str(uri).strip())
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if scheme not in {"http", "https"} or not host:
        raise BrowserOAuthError("OAuth redirect URI must be an absolute http:// or https:// URL.")
    if parsed.fragment:
        raise BrowserOAuthError("OAuth redirect URI must not contain a fragment.")
    if parsed.query:
        raise BrowserOAuthError("OAuth redirect URI must not contain a query string; providers return authorization parameters in the callback query.")
    path = parsed.path or "/"
    return scheme, host, parsed.port, path


def is_loopback_redirect(uri: str) -> bool:
    scheme, host, _port, _path = _normalized_callback_identity(uri)
    return scheme == "http" and host in {"localhost", "127.0.0.1", "::1"}


def validate_redirect_uri(uri: str) -> str:
    clean = str(uri).strip()
    scheme, host, port, _path = _normalized_callback_identity(clean)
    if scheme == "http" and host not in {"localhost", "127.0.0.1", "::1"}:
        raise BrowserOAuthError("Non-loopback OAuth redirect URIs must use HTTPS.")
    if host in {"localhost", "127.0.0.1", "::1"} and scheme == "http" and port is None:
        raise BrowserOAuthError("Loopback OAuth redirect URI must include an explicit port.")
    return clean


def parse_oauth_callback(callback_url: str, *, redirect_uri: str, expected_state: str) -> dict[str, str]:
    expected_identity = _normalized_callback_identity(redirect_uri)
    actual = urlsplit(str(callback_url).strip())
    actual_identity = (actual.scheme.lower(), (actual.hostname or "").lower(), actual.port, actual.path or "/")
    if actual_identity != expected_identity:
        raise BrowserOAuthError("OAuth callback URL does not match the registered redirect URI.")

    query = parse_qs(actual.query, keep_blank_values=True)

    def single(name: str, *, required: bool = False) -> str:
        values = query.get(name, [])
        if len(values) > 1:
            raise BrowserOAuthError(f"OAuth callback contains duplicate '{name}' parameters.")
        value = str(values[0]).strip() if values else ""
        if required and not value:
            raise BrowserOAuthError(f"OAuth callback is missing required '{name}'.")
        return value

    state = single("state", required=True)
    if not secrets.compare_digest(state, str(expected_state)):
        raise BrowserOAuthError("OAuth state validation failed; authorization was cancelled for safety.")

    error = single("error")
    if error:
        description = single("error_description") or error
        raise BrowserOAuthError(f"OAuth authorization was not completed: {description}")

    code = single("code", required=True)
    result: dict[str, str] = {"code": code, "state": state}
    for name, values in query.items():
        if name in result or not values:
            continue
        if len(values) == 1:
            result[name] = str(values[0]).strip()
    return result


class _LoopbackServer(HTTPServer):
    allow_reuse_address = False


class LoopbackOAuthReceiver:
    """Single-use HTTP loopback receiver for one OAuth authorization session."""

    def __init__(self, redirect_uri: str) -> None:
        clean = validate_redirect_uri(redirect_uri)
        if not is_loopback_redirect(clean):
            raise BrowserOAuthError("OAuth loopback receiver requires a loopback http:// redirect URI.")
        parsed = urlsplit(clean)
        host = parsed.hostname or "127.0.0.1"
        bind_host = "127.0.0.1" if host in {"localhost", "127.0.0.1"} else "::1"
        port = int(parsed.port or 0)
        path = parsed.path or "/"
        self.redirect_uri = clean
        self.expected_path = path
        self._callback_url = ""
        self._event = Event()
        self._cancel_event = Event()
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                request = urlsplit(self.path)
                if request.path != receiver.expected_path:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Not Found")
                    return
                registered = urlsplit(receiver.redirect_uri)
                receiver._callback_url = urlunsplit(
                    (registered.scheme, registered.netloc, request.path, request.query, "")
                )
                receiver._event.set()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(
                    b"<!doctype html><meta charset='utf-8'><title>Invio OAuth</title>"
                    b"<body style='font-family:Segoe UI,Arial,sans-serif;padding:32px'>"
                    b"<h2>Authorization received</h2>"
                    b"<p>You can return to Invio. This browser tab can be closed.</p></body>"
                )

            def log_message(self, _format: str, *_args) -> None:
                return

        try:
            self._server = _LoopbackServer((bind_host, port), Handler)
        except OSError as exc:
            raise BrowserOAuthError(
                f"OAuth callback port {port} is unavailable. Close the application using that port and try again."
            ) from exc
        self._server.timeout = 0.25

    def cancel(self) -> None:
        self._cancel_event.set()

    def close(self) -> None:
        self._server.server_close()

    def wait(self, timeout_seconds: int) -> str:
        deadline = time.monotonic() + max(10, int(timeout_seconds))
        try:
            while time.monotonic() < deadline and not self._event.is_set() and not self._cancel_event.is_set():
                self._server.handle_request()
            if self._cancel_event.is_set():
                raise BrowserOAuthError("OAuth authorization was cancelled.")
            if not self._event.is_set() or not self._callback_url:
                raise BrowserOAuthError("OAuth authorization timed out before the provider returned to Invio.")
            return self._callback_url
        finally:
            self._server.server_close()
