import urllib.request
import json
from agent_fabric.tools.decorator import tool

__all__ = ["fetch_hackernews_top"]


@tool("Fetch top stories from HackerNews")
def fetch_hackernews_top(limit: int = 5) -> str:
    """Retrieves top story titles and URLs from HackerNews Firebase API."""
    try:
        req = urllib.request.Request("https://hacker-news.firebaseio.com/v0/topstories.json", headers={"User-Agent": "AgentFabric/1.0"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            ids = json.loads(resp.read().decode("utf-8"))[:limit]
            
        stories = []
        for item_id in ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
            item_req = urllib.request.Request(item_url, headers={"User-Agent": "AgentFabric/1.0"})
            with urllib.request.urlopen(item_req, timeout=5.0) as item_resp:
                item = json.loads(item_resp.read().decode("utf-8"))
                title = item.get("title", "No title")
                url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")
                stories.append(f"- {title} ({url})")
                
        return "\n".join(stories)
    except Exception as e:
        return f"Failed to fetch HackerNews top stories: {e}"
