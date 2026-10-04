"""Kalibrr job board scraping (HTML server-rendered).

Job links follow the pattern: /id-ID/c/{company-slug}/jobs/{id}/{job-slug}
"""
import re

from bs4 import BeautifulSoup

from .base import fetch, clean

BASE = "https://www.kalibrr.com/id-ID/job-board"
JOB_LINK_RE = re.compile(r"^/id-ID/c/([^/]+)/jobs/(\d+)/([^/?#]+)")


def scrape(pages: int = 2) -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()
    for page in range(1, pages + 1):
        try:
            resp = fetch(f"{BASE}?page={page}")
        except Exception as e:
            print(f"[kalibrr] skip page {page}: {e}")
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=JOB_LINK_RE):
            href = a["href"]
            m = JOB_LINK_RE.match(href)
            if not m or href in seen:
                continue
            seen.add(href)
            company_slug, job_id, _ = m.groups()
            # Title: the h2 inside the card anchor; fallback to anchor text
            h2 = a.find("h2")
            title = clean(h2.get_text()) if h2 else ""
            if not title:
                texts = [clean(s) for s in a.stripped_strings if clean(s)]
                title = texts[0] if texts else ""
            if not title or len(title) < 3:
                continue
            # Company + location: pick from the card's text lines (skip title line)
            texts = [clean(s) for s in a.stripped_strings if clean(s)]
            company = texts[1] if len(texts) > 1 and texts[1] != title else ""
            location = ""
            for t in texts[2:5]:
                low = t.lower()
                if any(k in low for k in ["indonesia", "jakarta", "bandung", "surabaya", "yogyakarta",
                                          "semarang", "medan", "makassar", "remote", "bali", "tangerang",
                                          "bekasi", "depok", "bogor", "batam", " Bandung"]):
                    location = t
                    break
            is_remote = "remote" in (location + title).lower()
            jobs.append(
                {
                    "source": "kalibrr",
                    "title": title[:250],
                    "company": company[:150],
                    "location": location or "Indonesia",
                    "is_remote": is_remote,
                    "url": f"https://www.kalibrr.com{href}",
                    "posted_at": None,
                }
            )
    return jobs


if __name__ == "__main__":
    for j in scrape(1)[:10]:
        print(j)
