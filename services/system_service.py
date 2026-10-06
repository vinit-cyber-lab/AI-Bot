import requests

from config import GITHUB_TOKEN


def fetch_repo_summary(repo_name: str):
    url = f"https://api.github.com/repos/{repo_name}"
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[github] Request failed {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as exc:
        print(f"[github] Error: {exc}")
        return None
