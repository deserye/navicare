"""Fail if the repo contains a broken web link or a missing local asset.

Usage: python check_links.py
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SCAN_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml"}
SKIP_PARTS = {".venv", "venv", "__pycache__", ".git", "uploads"}
URL_RE = re.compile(r"https?://[^\s)\]>'\"<]+")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
SKIP_HOSTS = ("localhost", "127.0.0.1", "example.com", "example-llm.invalid")


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in SCAN_SUFFIXES:
            files.append(path)
    return files


def clean_url(raw: str) -> str:
    return raw.rstrip(".,);")


def collect_urls() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        for match in URL_RE.findall(text):
            url = clean_url(match)
            host = urlparse(url).netloc.lower()
            if any(
                host == skip or host.endswith("." + skip)
                for skip in ("localhost", "127.0.0.1")
            ):
                continue
            if any(skip in host for skip in SKIP_HOSTS):
                continue
            found.setdefault(url, []).append(str(path.relative_to(ROOT)))
    return found


def collect_local_links() -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for path in iter_files():
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in MD_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = (path.parent / target.split("#", 1)[0]).resolve()
            if not local.exists():
                missing.append((str(path.relative_to(ROOT)), target))
    return missing


def fetch(url: str) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NaviCareLinkCheck/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = getattr(response, "status", 200)
        final = response.geturl()
        raw = response.read(200_000)
    text = raw.decode("utf-8", "replace")
    parser = TitleParser()
    parser.feed(text)
    title = re.sub(r"\s+", " ", parser.title).strip()
    return status, final, title


def main() -> int:
    problems: list[str] = []
    import app

    if not app.STYLES_PATH.exists():
        problems.append("Missing asset: assets/styles.css")
    for stem in app.IMAGE_STEMS:
        picture = app.image_file(stem)
        if picture is None:
            problems.append(f"Missing image in assets/: {stem}")
            continue
        if picture.stat().st_size > app.MAX_RASTER_BYTES:
            problems.append(
                f"{picture.relative_to(ROOT)} is {picture.stat().st_size} bytes. "
                "Compress it with scripts/optimize_assets.py before deploying."
            )

    for source in app.OFFICIAL_SOURCES:
        if not source["url"].startswith("https://"):
            problems.append(f"Official source is not https: {source['url']}")

    for path, target in collect_local_links():
        problems.append(f"{path} links to missing file {target}")

    urls = collect_urls()
    if not urls:
        problems.append("No http(s) links were found to check.")

    for url, origins in sorted(urls.items()):
        where = ", ".join(sorted(set(origins)))
        try:
            status, final, title = fetch(url)
        except urllib.error.HTTPError as exc:
            problems.append(f"{url} -> HTTP {exc.code} ({where})")
            continue
        except Exception as exc:  # noqa: BLE001 - report every transport failure
            problems.append(f"{url} -> {type(exc).__name__}: {exc} ({where})")
            continue
        lowered = title.lower()
        if status >= 400 or "page not found" in lowered or "404" == lowered.strip():
            problems.append(
                f"{url} -> {status} title={title!r} final={final} ({where})"
            )
            continue
        print(f"OK {status} {url}")
        if title:
            print(f"   {title}")

    if problems:
        print("\nBroken links:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"\n{len(urls)} web links and {len(app.IMAGE_STEMS)} images checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
