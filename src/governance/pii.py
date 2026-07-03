"""
PII Detection & Redaction
============================
Simple regex-based detection for common PII patterns (emails, phone
numbers, SSNs, credit-card-like numbers). Used to redact sensitive data
before it's written to the audit log or returned in a response.

This is a lightweight, dependency-free first pass — good enough to catch
obvious leaks. A production system would layer in a proper NER/PII
model for names, addresses, etc.
"""
from __future__ import annotations

import re

_PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
}


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Redact any detected PII in text, returning the redacted text and
    a list of PII types found (for audit logging, not the actual values).

    Args:
        text: The text to scan.

    Returns:
        (redacted_text, list_of_pii_types_found)
    """
    found_types = []
    redacted = text
    for pii_type, pattern in _PATTERNS.items():
        if pattern.search(redacted):
            found_types.append(pii_type)
            redacted = pattern.sub(f"[REDACTED_{pii_type}]", redacted)
    return redacted, found_types