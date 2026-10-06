import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from functools import wraps
from config import (
    BOT_NAME,
    BOT_VERSION,
    DASHBOARD_HOST,
    DASHBOARD_PORT,
    DASHBOARD_DEBUG,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    GITHUB_REPO,
)
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status

app = Flask(__name__)
app.secret_key = "ai-bot-secret-key-2024"


def check_auth(username, password):
    """Verify basic auth credentials"""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def authenticate():
    """Return 401 with basic auth challenge"""
    return (
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="AI-Bot Dashboard"'},
    )


def requires_auth(f):
    """Decorator to protect routes with basic authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route("/")
@requires_auth
def index():
    """Main dashboard page"""
    status = {
        "bot_name": BOT_NAME,
        "bot_version": BOT_VERSION,
        "status": "running",
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render_template("index.html", status=status)


@app.route("/api/status")
@requires_auth
def api_status():
    """Get bot status"""
    return jsonify(
        {
            "bot_name": BOT_NAME,
            "bot_version": BOT_VERSION,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/health")
@requires_auth
def api_health():
    """Get system health metrics"""
    stats = get_system_status()
    if not stats:
        return jsonify({"error": "Failed to retrieve system stats"}), 500

    return jsonify(
        {
            "cpu_percent": stats.get("cpu_percent", 0),
            "memory_percent": stats.get("memory_percent", 0),
            "disk_percent": stats.get("disk_percent", 0),
            "platform": stats.get("platform", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/github")
@requires_auth
def api_github():
    """Get GitHub repository information"""
    repo_info = fetch_repo_summary(GITHUB_REPO)
    if not repo_info:
        return (
            jsonify({"error": f"Failed to fetch repository {GITHUB_REPO}"}),
            500,
        )

    return jsonify(
        {
            "repository": repo_info.get("full_name", GITHUB_REPO),
            "description": repo_info.get("description", "N/A"),
            "default_branch": repo_info.get("default_branch", "unknown"),
            "visibility": repo_info.get("visibility", "unknown"),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "watchers": repo_info.get("watchers_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "created_at": repo_info.get("created_at", "unknown"),
            "last_push": repo_info.get("pushed_at", "unknown"),
            "url": repo_info.get("html_url", "#"),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/dashboard")
@requires_auth
def api_dashboard():
    """Get all dashboard data at once"""
    repo_info = fetch_repo_summary(GITHUB_REPO)
    system_stats = get_system_status()

    dashboard_data = {
        "bot": {
            "name": BOT_NAME,
            "version": BOT_VERSION,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        },
        "github": None,
        "system": None,
    }

    if repo_info:
        dashboard_data["github"] = {
            "repository": repo_info.get("full_name", GITHUB_REPO),
            "description": repo_info.get("description", "N/A"),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "last_push": repo_info.get("pushed_at", "unknown"),
            "url": repo_info.get("html_url", "#"),
        }

    if system_stats:
        dashboard_data["system"] = {
            "cpu_percent": system_stats.get("cpu_percent", 0),
            "memory_percent": system_stats.get("memory_percent", 0),
            "disk_percent": system_stats.get("disk_percent", 0),
            "platform": system_stats.get("platform", "unknown"),
        }

    return jsonify(dashboard_data)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print(f"Starting {BOT_NAME} Dashboard...")
    print(f"Access at: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"Username: {ADMIN_USERNAME}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=DASHBOARD_DEBUG)
