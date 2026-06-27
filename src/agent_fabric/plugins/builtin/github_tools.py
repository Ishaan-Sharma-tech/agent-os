import urllib.request
import json
from agent_fabric.tools.decorator import tool

__all__ = ["get_github_repo_info"]


@tool("Get basic metadata for a public GitHub repository")
def get_github_repo_info(owner: str, repo: str) -> str:
    """Fetches star count, description, open issues, and language for a public GitHub repo."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        req = urllib.request.Request(url, headers={"User-Agent": "AgentFabric/1.0", "Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        name = data.get("full_name", f"{owner}/{repo}")
        desc = data.get("description", "No description")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        issues = data.get("open_issues_count", 0)
        lang = data.get("language", "Unknown")
        
        return f"Repository: {name}\nDescription: {desc}\nLanguage: {lang}\nStars: {stars} | Forks: {forks} | Open Issues: {issues}"
    except Exception as e:
        return f"Failed to fetch GitHub repo info for '{owner}/{repo}': {e}"
