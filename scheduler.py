"""Scheduler: run all scrapers -> classify -> dedup -> dispatch to matching users."""
import logging
import os
import time

import db
from bot import send_job_message
from classifier import classify, classify_location
from scraper import glints, kalibrr, remoteok, remotive, wwr

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("scheduler")

SOURCES = [remoteok.scrape, remotive.scrape, wwr.scrape, kalibrr.scrape, glints.scrape]


def run_cycle(token: str | None = None) -> dict:
    """One scrape+dispatch cycle. Returns stats."""
    db.init_db()
    new_jobs: list[dict] = []
    total_fetched = 0

    for scrape_fn in SOURCES:
        try:
            fetched = scrape_fn()
            total_fetched += len(fetched)
        except Exception as e:
            log.error(f"{scrape_fn.__module__} failed: {e}")
            continue
        for item in fetched:
            if not item.get("url") or not item.get("title"):
                continue
            category = classify(item["title"], item.get("company", ""))
            location = item.get("location", "")
            loc_cat = classify_location(location, item.get("is_remote", False))
            job_id = db.insert_job(
                source=item["source"],
                title=item["title"],
                company=item.get("company", ""),
                location=location,
                is_remote=item.get("is_remote", False),
                url=item["url"],
                category=category,
                posted_at=item.get("posted_at"),
            )
            if job_id is None:
                continue  # duplicate
            item["id"] = job_id
            item["category"] = category
            item["loc_cat"] = loc_cat
            new_jobs.append(item)

    log.info(f"fetched={total_fetched} new={len(new_jobs)}")

    sent = 0
    if token and new_jobs:
        for job in new_jobs:
            full_job = {
                "title": job["title"],
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "is_remote": job.get("is_remote", False),
                "category": job["category"],
                "source": job["source"],
                "url": job["url"],
                "id": job["id"],
            }
            for user_id in db.find_matching_users(job["category"], job.get("is_remote", False), job.get("location", "")):
                try:
                    if send_job_message(token, user_id, full_job):
                        db.mark_delivered(user_id, job["id"])
                        sent += 1
                    time.sleep(0.05)  # respect Telegram rate limits (~30 msg/s)
                except Exception as e:
                    log.warning(f"send to {user_id} failed: {e}")

    stats = db.job_stats()
    stats.update({"fetched": total_fetched, "new": len(new_jobs), "sent": sent})
    log.info(f"cycle done: {stats}")
    return stats


def main() -> None:
    token = os.environ.get("BOT_TOKEN", "")
    while True:
        try:
            run_cycle(token or None)
        except Exception as e:
            log.error(f"cycle crashed: {e}")
        log.info("sleeping 3600s...")
        time.sleep(3600)


if __name__ == "__main__":
    main()
