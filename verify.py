"""End-to-end verification: DB contents + matching logic."""
import db

db.init_db()
jobs = db.latest_jobs(15)
print("total jobs fetched:", len(jobs))
for j in jobs:
    print(f"[{j['source']:8}] {j['title'][:55]:55} | cat={j['category']:9} | remote={j['is_remote']}")

db.upsert_user(12345, "testuser")
db.set_preferences(12345, "it", "any", True)
m1 = db.find_matching_users("it", True, "Worldwide")
print("match test (it/remote user, it remote job):", m1 == [12345])
m2 = db.find_matching_users("it", False, "Jakarta")
print("match test (non-remote job vs remote-only user):", m2 == [])
db.mark_delivered(12345, jobs[0]["id"])
print("delivery marked:", db.already_delivered(12345, jobs[0]["id"]))
