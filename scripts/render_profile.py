#!/usr/bin/env python3
"""Render the profile README and its SVG cards.

Standard library only; GitHub Actions runs this daily with GITHUB_TOKEN. Each
data source falls back to the snapshot in data/status.json on its own, so the
page still renders when an API call fails.

    python scripts/render_profile.py            # live data
    python scripts/render_profile.py --offline  # snapshot only

Fonts, the header plate and screenshots are prepared once by
scripts/prepare_assets.py and committed under assets/src/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio import data as live  # noqa: E402
from studio.readme import build  # noqa: E402
from studio.svg import ROOT  # noqa: E402

ASSETS = ROOT / "assets"
README = ROOT / "README.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="render from data/status.json only")
    args = parser.parse_args()
    data = live.collect(live.load_config(), os.environ.get("GITHUB_TOKEN"), offline=args.offline)
    files, readme = build(data)
    for name, content in files.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
    README.write_text(readme, encoding="utf-8")
    sources = ", ".join(f"{name} {state}" for name, state in data["sources"].items()) or "snapshot only"
    print(f"wrote {len(files)} SVGs and README.md ({sources})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
