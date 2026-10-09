"""Shrink NaviCare pictures so they can be committed and deployed.

The original exports were too large to upload. This writes web-sized files
next to app.py. The running app uses a file when it exists and stays under
1.5 MB; otherwise it keeps the built-in SVG.

Install Pillow first: python -m pip install pillow

Example:
    python scripts/optimize_assets.py --hero ~/Downloads/hero.jpg --scheme ~/Downloads/scheme.jpg --conversation ~/Downloads/conversation.jpg --logo ~/Downloads/logo.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
MAX_BYTES = 400_000
MAX_EDGE = 1400

try:
    from PIL import Image
except ImportError:
    print("Install Pillow first: python -m pip install pillow", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> Image.Image:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return Image.open(path)


def save_under_limit(image: Image.Image, dest: Path, kind: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    working = image.copy()
    edge = MAX_EDGE
    for _ in range(8):
        current = working.copy()
        current.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        if kind == "jpeg":
            current = current.convert("RGB")
            for quality in (85, 75, 65, 55, 45):
                current.save(
                    dest, "JPEG", quality=quality, optimize=True, progressive=True
                )
                if dest.stat().st_size <= MAX_BYTES:
                    return
        else:
            current.save(dest, "PNG", optimize=True)
            if dest.stat().st_size <= MAX_BYTES:
                return
        edge = int(edge * 0.75)
    raise SystemExit(
        f"Could not shrink {dest.name} under {MAX_BYTES} bytes. Start from a smaller image."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress NaviCare images for GitHub and Streamlit."
    )
    parser.add_argument("--hero", type=Path, help="Large hero image")
    parser.add_argument("--scheme", type=Path, help="Large scheme illustration")
    parser.add_argument(
        "--conversation", type=Path, help="Large conversation illustration"
    )
    parser.add_argument("--logo", type=Path, help="Large logo")
    args = parser.parse_args()
    if not any((args.hero, args.scheme, args.conversation, args.logo)):
        parser.error("Pass at least one of --hero, --scheme, --conversation, or --logo")

    jobs = [
        (args.hero, ASSET_DIR / "navicare_hero.jpg", "jpeg"),
        (args.scheme, ASSET_DIR / "navicare_scheme.jpg", "jpeg"),
        (args.conversation, ASSET_DIR / "navicare_conversation.jpg", "jpeg"),
        (args.logo, ASSET_DIR / "navicare_logo_mark.png", "png"),
    ]
    for source, dest, kind in jobs:
        if source is None:
            continue
        before = source.stat().st_size
        save_under_limit(load(source), dest, kind)
        for suffix in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
            sibling = dest.with_suffix(suffix)
            if sibling != dest and sibling.exists():
                sibling.unlink()
        after = dest.stat().st_size
        print(
            f"{source.name}: {before // 1024} KB -> {dest.relative_to(ROOT)} {after // 1024} KB"
        )


if __name__ == "__main__":
    main()
