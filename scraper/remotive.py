"""Remotive official API: https://remotive.com/api/remote-jobs"""
from .base import fetch, clean


def scrape(limit: int = 40) -> list[dict]:
    data = fetch("https://remotive.com/api/remote-jobs?limit=50").json()
    jobs = []
    for item in data.get("jobs", [])[:limit]:
        jobs.append(
            {
                "source": "remotive",
                "title": clean(item.get("title")),
                "company": clean(item.get("company_name")),
                "location": clean(item.get("candidate_required_location")) or "Worldwide (Remote)",
                "is_remote": True,
                "url": clean(item.get("url")),
                "posted_at": int(item["pub_date_ts"]) if item.get("pub_date_ts") else None,
            }
        )
    return jobs


if __name__ == "__main__":
    for j in scrape(5):
        print(j)
