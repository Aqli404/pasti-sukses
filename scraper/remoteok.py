"""RemoteOK official API: https://remoteok.com/api"""
from .base import fetch, clean


def scrape(limit: int = 40) -> list[dict]:
    data = fetch("https://remoteok.com/api").json()
    jobs = []
    for item in data:
        if not isinstance(item, dict) or not item.get("position"):
            continue  # first element is a legal notice
        jobs.append(
            {
                "source": "remoteok",
                "title": clean(item.get("position")),
                "company": clean(item.get("company")),
                "location": "Worldwide (Remote)",
                "is_remote": True,
                "url": clean(item.get("url")) or f"https://remoteok.com/remote-jobs/{item.get('slug','')}",
                "posted_at": int(item["epoch"]) if item.get("epoch") else None,
            }
        )
        if len(jobs) >= limit:
            break
    return jobs


if __name__ == "__main__":
    for j in scrape(5):
        print(j)
