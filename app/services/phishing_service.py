"""Explainable phishing-risk heuristics for URLs — adapted from ai-cyber-account-lab.

Risk signals only: a flag does not prove a link is malicious, and a clean
result does not prove it is safe.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = ["login", "verify", "secure", "update", "confirm", "account"]


def assess_url(url: str) -> dict:
    reasons: list[str] = []
    score = 0
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()

    if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", host):
        score += 2
        reasons.append("Host is a raw IP address instead of a domain name.")
    if parsed.scheme != "https":
        score += 1
        reasons.append("Link does not use HTTPS.")
    if host.count(".") >= 3:
        score += 1
        reasons.append("Many subdomains can hide the real domain.")
    if "-" in host and any(w in host for w in SUSPICIOUS_WORDS):
        score += 1
        reasons.append("Domain mixes security words with hyphens, a common look-alike trick.")
    if "@" in url:
        score += 2
        reasons.append("URL contains '@', which can hide the real destination.")
    if len(url) > 100:
        score += 1
        reasons.append("Unusually long URL.")

    return {"url": url, "risk_score": score, "is_suspicious": score >= 2, "reasons": reasons}
