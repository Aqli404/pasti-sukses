"""We Work Remotely official RSS feeds."""
import re
import xml.etree.ElementTree as ET

from .base import fetch, clean

FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
    "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss",
]

REGION_RE = re.compile(r"Region", re.I)


def scrape(limit_per_feed: int = 15) -> list[dict]:
    jobs = []
    for feed in FEEDS:
        try:
            root = ET.fromstring(fetch(feed).content)
        except Exception as e:
            print(f"[wwr] skip feed {feed}: {e}")
            continue
        for item in root.iter("item"):
            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            if not title or not link:
                continue
            # title format: "Company: Job Title ( Region )"
            company, _, rest = title.partition(":")
            job_title = rest.strip() or title
            is_remote = True  # all WWR jobs are remote
            region = ""
            m = re.search(r"\(([^)]*)\)\s*$", job_title)
            if m:
                region = m.group(1).strip()
                job_title = job_title[: m.start()].strip()
            jobs.append(
                {
                    "source": "wwr",
                    "title": job_title,
                    "company": company.strip(),
                    "location": f"Remote - {region}" if region else "Remote",
                    "is_remote": is_remote,
                    "url": link,
                    "posted_at": None,
                }
            )
            if len([j for j in jobs if j["source"] == "wwr"]) >= limit_per_feed:
                break
    return jobs


if __name__ == "__main__":
    for j in scrape(5):
        print(j)
