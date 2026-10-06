"""Write the real linkedin.py scraper for /opt/pasti-sukses and register it in scheduler.

Uses the public LinkedIn guest jobs endpoint (no login, no protected JobStreet scraping).
Strategy: one query per agro/keyword group, paginated start=0,25; classify with existing classifier.
"""
import re
import html as htmllib
import time

import requests

from .base import clean

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}
GUEST_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# Search terms chosen to cover the 'agro' category keywords
SEARCH_TERMS = ["pertanian", "pangan", "agribisnis", "agronomi", "quality control"]

CARD_SPLIT = re.compile(r'<div class="base-card ')
RE_LINK = re.compile(r'href="(https://[^"]+?/jobs/view/[^"?]+)')
RE_TITLE = re.compile(r'<h3 class="base-search-card__title">\s*(.*?)\s*</h3>', re.S)
RE_COMPANY = re.compile(r'<h4 class="base-search-card__subtitle">.*?<a[^>]*>(.*?)</a>', re.S)
RE_LOC = re.compile(r'<span class="job-search-card__location">\s*(.*?)\s*</span>', re.S)
RE_DATE = re.compile(r'datetime="([^"]+)"')


def _parse_cards(html_text: str) -> list[dict]:
    jobs = []
    for block in CARD_SPLIT.split(html_text)[1:]:
        link = RE_LINK.search(block)
        title = RE_TITLE.search(block)
        if not link or not title:
            continue
        company = RE_COMPANY.search(block)
        loc = RE_LOC.search(block)
        date = RE_DATE.search(block)
        location = htmllib.unescape(loc.group(1)).strip() if loc else "Indonesia"
        import calendar
        posted_at = None
        if date:
            try:
                posted_at = calendar.timegm(time.strptime(date.group(1), "%Y-%m-%d"))
            except ValueError:
                posted_at = None
        jobs.append(
            {
                "source": "linkedin",
                "title": clean(htmllib.unescape(title.group(1)).strip())[:250],
                "company": clean(htmllib.unescape(company.group(1)).strip())[:150] if company else "",
                "location": location,
                "is_remote": "remote" in location.lower(),
                "url": link.group(1),
                "posted_at": posted_at,
            }
        )
    return jobs


def scrape(limit: int = 25) -> list[dict]:
    """One page (start=0) per search term; guest API caps results at ~25 per query."""
    jobs: list[dict] = []
    seen: set[str] = set()
    for term in SEARCH_TERMS:
        try:
            resp = requests.get(
                GUEST_URL,
                params={"keywords": term, "location": "Indonesia", "start": 0},
                headers=UA,
                timeout=20,
            )
            if resp.status_code != 200:
                print(f"[linkedin] term={term!r} HTTP {resp.status_code}")
                continue
            for job in _parse_cards(resp.text):
                if job["url"] in seen:
                    continue
                seen.add(job["url"])
                jobs.append(job)
        except Exception as e:
            print(f"[linkedin] term={term!r} failed: {e}")
        time.sleep(1.5)  # be gentle with the guest endpoint
    return jobs


if __name__ == "__main__":
    import json

    result = scrape()
    print(f"total: {len(result)}")
    print(json.dumps(result[:3], indent=2, ensure_ascii=False))
