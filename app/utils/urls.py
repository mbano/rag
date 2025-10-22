from urllib.parse import urlparse
import hashlib
import re


def url_to_resource_name(url: str) -> str:
    parsed = urlparse(url)
    slug = parsed.netloc + parsed.path
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", slug).strip("_")
    short_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{slug}_{short_hash}"
