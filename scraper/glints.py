"""Glints job board scraping (Next.js / JSON payloads)."""
from .base import fetch, clean

API = "https://glints.com/api/graph/v1"


def scrape(limit: int = 40) -> list[dict]:
    """Glints uses a GraphQL-ish endpoint; fall back to sitemap-free HTML parse on failure."""
    payload = {
        "query": """
        query SearchOpportunities($input: SearchOpportunitiesInput!) {
          searchOpportunities(input: $input) {
            opportunities {
              id title
              company { name }
              location
              createdAt
            }
          }
        }
        """,
        "variables": {"input": {"page": 1, "limit": limit, "countries": ["ID"]}},
    }
    jobs: list[dict] = []
    try:
        resp = fetch(API, json=payload)
        data = resp.json()
        opps = (
            data.get("data", {})
            .get("searchOpportunities", {})
            .get("opportunities", [])
        )
        for o in opps:
            jobs.append(
                {
                    "source": "glints",
                    "title": clean(o.get("title")),
                    "company": clean((o.get("company") or {}).get("name")),
                    "location": clean(o.get("location")) or "Indonesia",
                    "is_remote": "remote" in (o.get("location") or "").lower(),
                    "url": f"https://glints.com/id/opportunities/jobs/{o.get('id')}",
                    "posted_at": None,
                }
            )
        return jobs
    except Exception as e:
        print(f"[glints] API failed ({e}); trying HTML fallback")
    return _html_fallback(limit)


def _html_fallback(limit: int) -> list[dict]:
    from bs4 import BeautifulSoup

    try:
        resp = fetch("https://glints.com/id/opportunities/jobs")
    except Exception as e:
        print(f"[glints] HTML fallback failed: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for a in soup.select("a[href*='/opportunities/jobs/']"):
        title = clean(a.get_text())
        href = a.get("href", "")
        if not title or not href:
            continue
        url = "https://glints.com" + href if href.startswith("/") else href
        jobs.append(
            {
                "source": "glints",
                "title": title[:200],
                "company": "",
                "location": "Indonesia",
                "is_remote": "remote" in title.lower(),
                "url": url,
                "posted_at": None,
            }
        )
        if len(jobs) >= limit:
            break
    return jobs


if __name__ == "__main__":
    for j in scrape(5):
        print(j)
