from functools import wraps
from flask import request, jsonify
import os

from services.database import log_audit
from services.security_layer import check_rate_limit, log_security_event


def require_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            log_security_event("AUTH_FAILURE", "unknown", "missing_credentials", result="failed")
            return jsonify({"error": "Authentication required"}), 401

        admin_user = os.getenv("DASHBOARD_ADMIN_USER", "admin")
        admin_pass = os.getenv("DASHBOARD_ADMIN_PASS", "admin123")

        if auth.username != admin_user or auth.password != admin_pass:
            log_security_event("AUTH_FAILURE", auth.username or "unknown", "invalid_credentials", result="failed")
            return jsonify({"error": "Invalid credentials"}), 401

        log_security_event("AUTH_SUCCESS", auth.username, "login")
        return f(*args, **kwargs)

    return decorated


def require_rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        actor = auth.username if auth else "unknown"

        if not check_rate_limit(actor, limit=10, window_seconds=60):
            log_security_event("RATE_LIMIT_EXCEEDED", actor, request.path, result="failed")
            return jsonify({"error": "Rate limit exceeded"}), 429

        return f(*args, **kwargs)

    return decorated


def log_admin_action(action: str, target: str = "", details: str = ""):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            actor = auth.username if auth else "system"
            ip = request.remote_addr

            try:
                result = f(*args, **kwargs)
                log_audit(action, actor, target, details, success=True, ip_address=ip)
                log_security_event("ADMIN_ACTION", actor, action, target, "success", details)
                return result
            except Exception as exc:
                log_audit(action, actor, target, str(exc), success=False, ip_address=ip)
                log_security_event("ADMIN_ACTION", actor, action, target, "failed", str(exc))
                raise

        return decorated

    return decorator
