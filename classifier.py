"""Simple keyword-based job category classifier (no external deps)."""
import re

FIELD_KEYWORDS = {
    "it": [
        "software", "engineer", "developer", "dev", "programmer", "backend", "frontend",
        "fullstack", "full-stack", "mobile", "android", "ios", "qa", "tester", "devops",
        "data engineer", "data scientist", "analyst", "machine learning", "ai", "cloud",
        "security", "sysadmin", "network engineer", "web", "it ", "informatics",
        "python", "java", "javascript", "php", "golang", "react", "flutter",
    ],
    "design": [
        "designer", "design", "ui", "ux", "graphic", "illustrator", "motion",
        "video editor", "creative", "3d", "animator",
    ],
    "marketing": [
        "marketing", "social media", "seo", "content writer", "copywriter", "digital",
        "ads", "advertising", "brand", "community", "growth", "pr ", "public relations",
        "sales", "business development", "partnership",
    ],
    "finance": [
        "finance", "accounting", "accountant", "tax", "audit", "bookkeeping",
        "financial", "treasury", "payable", "receivable",
    ],
}


def classify(title: str, company: str = "", location: str = "") -> str:
    text = f"{title} {company}".lower()
    scores = {}
    for field, keywords in FIELD_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw.strip()) + r"\b", text):
                score += 1
        if score:
            scores[field] = score
    if scores:
        return max(scores, key=scores.get)
    return "other"


def classify_location(location: str, is_remote: bool) -> str:
    if is_remote:
        return "remote"
    loc = (location or "").lower()
    for city in ["jakarta", "bandung", "surabaya", "yogyakarta", "semarang", "medan", "makassar"]:
        if city in loc:
            return city
    return "other"


if __name__ == "__main__":
    tests = [
        ("Senior Backend Engineer (Python)", "", False, "it"),
        ("UI/UX Designer", "Tokopedia", False, "design"),
        ("Social Media Specialist", "", False, "marketing"),
        ("Staff Accounting", "", False, "finance"),
        ("Warehouse Staff", "", False, "other"),
        ("Frontend Developer", "", True, "it"),
    ]
    for title, company, remote, expected in tests:
        got = classify(title, company)
        assert got == expected, f"classify({title!r}) = {got}, want {expected}"
    assert classify_location("Remote - Worldwide", True) == "remote"
    assert classify_location("Jakarta Selatan", False) == "jakarta"
    print("classifier self-check OK")
