"""Shared HTTP + normalisation helpers for scrapers."""
import time

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

TIMEOUT = 25


def fetch(url: str, **kwargs) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    time.sleep(1)  # polite delay
    return resp


def clean(text: str | None) -> str:
    return " ".join((text or "").split())
