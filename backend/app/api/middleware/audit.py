"""Audit logging middleware for tracking all API operations."""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit trail."""

    # Paths to exclude from detailed logging
    EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    # Sensitive headers to mask
    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}

    def __init__(self, app):
        super().__init__(app)
        self._audit_logs: list = []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        request_id = str(uuid4())
        start_time = time.time()

        # Capture request metadata
        audit_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_type": request.headers.get("content-type"),
        }

        # Extract user info from token if available
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_token
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                audit_entry["user_id"] = payload.get("sub")
                audit_entry["user_email"] = payload.get("email")
                audit_entry["user_role"] = payload.get("role")
            except Exception:
                audit_entry["user_id"] = "unauthenticated"

        # Add request ID to request state
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)

            # Capture response metadata
            duration = time.time() - start_time
            audit_entry["status_code"] = response.status_code
            audit_entry["duration_ms"] = round(duration * 1000, 2)
            audit_entry["success"] = 200 <= response.status_code < 400

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Determine action type
            audit_entry["action"] = self._determine_action(
                request.method, request.url.path
            )

            # Log based on severity
            if response.status_code >= 500:
                logger.error(f"AUDIT: {json.dumps(audit_entry)}")
            elif response.status_code >= 400:
                logger.warning(f"AUDIT: {json.dumps(audit_entry)}")
            else:
                logger.info(f"AUDIT: {json.dumps(audit_entry)}")

            # Store audit entry
            self._audit_logs.append(audit_entry)

            # Keep only last 10000 entries in memory
            if len(self._audit_logs) > 10000:
                self._audit_logs = self._audit_logs[-10000:]

            return response

        except Exception as e:
            duration = time.time() - start_time
            audit_entry["status_code"] = 500
            audit_entry["duration_ms"] = round(duration * 1000, 2)
            audit_entry["success"] = False
            audit_entry["error"] = str(e)

            logger.error(f"AUDIT ERROR: {json.dumps(audit_entry)}")
            self._audit_logs.append(audit_entry)

            raise

    def _determine_action(self, method: str, path: str) -> str:
        """Determine the audit action based on method and path."""
        path_parts = path.strip("/").split("/")

        # Map paths to actions
        action_map = {
            ("POST", "auth", "login"): "USER_LOGIN",
            ("POST", "auth", "register"): "USER_REGISTER",
            ("POST", "auth", "logout"): "USER_LOGOUT",
            ("POST", "auth", "refresh"): "TOKEN_REFRESH",
            ("POST", "contracts", "generate"): "CONTRACT_GENERATE",
            ("POST", "contracts", "upload"): "CONTRACT_UPLOAD",
            ("GET", "contracts"): "CONTRACT_VIEW",
            ("PUT", "contracts"): "CONTRACT_UPDATE",
            ("DELETE", "contracts"): "CONTRACT_DELETE",
            ("POST", "review", "risk-analysis"): "RISK_ANALYSIS",
            ("POST", "compliance", "check"): "COMPLIANCE_CHECK",
            ("POST", "versions"): "VERSION_CREATE",
            ("POST", "versions", "merge"): "VERSION_MERGE",
            ("POST", "versions", "approve"): "VERSION_APPROVE",
        }

        # Try to match the action
        for (m, *parts), action in action_map.items():
            if method == m and all(p in path_parts for p in parts):
                return action

        # Default actions based on method
        method_actions = {
            "GET": "READ",
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        return method_actions.get(method, "UNKNOWN")

    def get_audit_logs(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> list:
        """Retrieve audit logs with optional filtering."""
        logs = self._audit_logs.copy()

        if user_id:
            logs = [l for l in logs if l.get("user_id") == user_id]
        if action:
            logs = [l for l in logs if l.get("action") == action]
        if start_date:
            logs = [l for l in logs if l.get("timestamp", "") >= start_date]

        # Return most recent first
        logs.reverse()
        return logs[:limit]
