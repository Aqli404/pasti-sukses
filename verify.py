"""End-to-end verification: DB contents + matching + saved_jobs + HTML sanitisation."""
import html

import db

db.init_db()

# --- jobs present ---
jobs = db.latest_jobs(5)
print("jobs in db (sample):", len(jobs))
for j in jobs:
    print(f"[{j['source']:8}] cat={j['category']:10} remote={j['is_remote']} | {j['title'][:50]}")

# --- matching logic ---
db.upsert_user(12345, "testuser")
db.set_preferences(12345, "it", "any", True)
m1 = db.find_matching_users("it", True, "Worldwide")
assert 12345 in m1, f"expected 12345 in results, got {m1}"
m2 = db.find_matching_users("it", False, "Jakarta")
assert m2 == [], f"remote-only user should not match onsite job, got {m2}"
print("matching logic OK")

# --- new categories accepted in matching ---
db.upsert_user(777, "agrofan")
db.set_preferences(777, "agro", "any", False)
db.upsert_user(888, "opsfan")
db.set_preferences(888, "operations", "any", False)
assert 777 in db.find_matching_users("agro", False, "Indonesia")
assert 888 in db.find_matching_users("operations", True, "Remote")
print("agro & operations matching OK")

# --- saved_jobs: save / list / is_saved / unsave ---
assert len(jobs) > 0, "no jobs in db to test saved_jobs"
job_id = jobs[0]["id"]
db.save_job(12345, job_id)
assert db.is_saved(12345, job_id) is True
saved = db.get_saved_jobs(12345)
assert any(j["id"] == job_id for j in saved), "saved job not in list"
db.unsave_job(12345, job_id)
assert db.is_saved(12345, job_id) is False
db.unsave_job(12345, job_id)  # idempotent
db.save_job(99999, job_id)    # orphan user is tolerated (no FK enforcement pragma)
db.unsave_job(99999, job_id)
print("saved_jobs save/list/unsave OK")

# --- HTML sanitisation: nasty title must not break markup ---
from bot import job_text

nasty = {
    "title": 'Bagi2 <b>GRATIS</b> & "reseller"_ [aman] *minta* mods `cmd`',
    "company": "PT <> & 'Quote' _Test_",
    "location": "Jakarta [Pusat] *Utara*",
    "is_remote": False,
    "category": "it",
    "source": "kalibrr",
    "url": "https://example.com/a?b=1&c=2",
    "id": 1,
}
text = job_text(nasty)
assert "&lt;b&gt;GRATIS&lt;/b&gt;" in text, "title not escaped"
assert "&amp;" in text, "ampersand not escaped"
assert "&lt;&gt;" in text, "angle brackets not escaped"
assert "&quot;reseller&quot;" in text, "double quote not escaped"
assert 'href="https://example.com/a?b=1&amp;c=2"' in text, "url not quote-escaped"
assert text.count("<b>") == 1 and text.count("</b>") == 1, "unexpected tag count"
assert "<a href=" in text and "</a>" in text, "link markup missing"
print("HTML sanitisation OK (no raw special chars break markup)")

# cleanup test rows
import sqlite3
conn = sqlite3.connect(db.DB_PATH)
conn.execute("DELETE FROM saved_jobs WHERE user_id IN (12345, 99999)")
conn.execute("DELETE FROM preferences WHERE user_id IN (12345, 777, 888)")
conn.execute("DELETE FROM users WHERE user_id IN (12345, 777, 888)")
conn.commit()
conn.close()
print("cleanup OK")
print("ALL VERIFICATIONS PASSED")
