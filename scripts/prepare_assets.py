#!/usr/bin/env python3
"""Prepare the static inputs that the daily renderer embeds.

Run locally, not in CI: it needs Pillow, NumPy, OpenCV and fontTools. The
outputs under assets/src/ are committed, so render_profile.py can stay on the
standard library.

    python scripts/prepare_assets.py --fonts DIR --header --grain --autokeeper-img DIR

DIR for --fonts holds the variable TTFs from google/fonts (OFL):
CormorantGaramond[wght].ttf, CormorantGaramond-Italic[wght].ttf and
JetBrainsMono[wght].ttf, plus their OFL-*.txt licenses. Text is drawn as glyph
outlines, so the cards need no web fonts and the renderer can measure every
line it sets.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "src"

# Every string the renderer draws is Latin; live data (repo names, dates,
# counts) is ASCII. A fixed character set lets CI render without fontTools.
CHARSET = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "".join(chr(c) for c in range(0xA0, 0x100))
    + "–—‘’“”•…′″‰←↑→↓↗↘±×÷−≈≤≥ΔΣ√∞⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄π·◆◇●■□▲▼"
    + "αβγδεθλμσφω"
)

FONTS = [
    # (face key used by the renderer, source file, weight)
    ("serif", "CormorantGaramond[wght].ttf", 600),
    ("serif-m", "CormorantGaramond[wght].ttf", 500),
    ("italic", "CormorantGaramond-Italic[wght].ttf", 500),
    ("mono", "JetBrainsMono[wght].ttf", 500),
    ("mono-b", "JetBrainsMono[wght].ttf", 700),
]


def kerning(font, names: dict[str, str]) -> dict[str, int]:
    """Flatten the GPOS kern feature to pair values for the glyphs we draw."""
    if "GPOS" not in font:
        return {}
    gpos = font["GPOS"].table
    lookups = sorted({
        index
        for record in gpos.FeatureList.FeatureRecord
        if record.FeatureTag == "kern"
        for index in record.Feature.LookupListIndex
    })
    by_glyph = {glyph: char for char, glyph in names.items()}
    glyphs = list(by_glyph)
    pairs: dict[tuple[str, str], int] = {}
    for index in lookups:
        lookup = gpos.LookupList.Lookup[index]
        decided: set[tuple[str, str]] = set()
        for table in lookup.SubTable:
            if lookup.LookupType == 9:
                table = table.ExtSubTable
            if getattr(table, "LookupType", 2) != 2:
                continue
            covered = set(table.Coverage.glyphs)
            for first in glyphs:
                if first not in covered:
                    continue
                if table.Format == 1:
                    pair_set = table.PairSet[table.Coverage.glyphs.index(first)]
                    for record in pair_set.PairValueRecord:
                        key = (first, record.SecondGlyph)
                        if record.SecondGlyph in by_glyph and key not in decided:
                            decided.add(key)
                            value = getattr(record.Value1, "XAdvance", 0) if record.Value1 else 0
                            pairs[key] = pairs.get(key, 0) + value
                else:
                    class1 = table.ClassDef1.classDefs.get(first, 0)
                    for second in glyphs:
                        key = (first, second)
                        if key in decided:
                            continue
                        decided.add(key)
                        record = table.Class1Record[class1].Class2Record[table.ClassDef2.classDefs.get(second, 0)]
                        value = getattr(record.Value1, "XAdvance", 0) if record.Value1 else 0
                        if value:
                            pairs[key] = pairs.get(key, 0) + value
    return {by_glyph[a] + by_glyph[b]: v for (a, b), v in pairs.items() if v}


def compact_path(d: str) -> str:
    """Round outline coordinates to whole font units (1/1000 em is far below a pixel)."""
    d = re.sub(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", lambda m: str(round(float(m.group()))), d)
    d = re.sub(r" ?(-)", r"\1", d)  # "10 -20" -> "10-20"
    return re.sub(r"([A-Za-z]) ", r"\1", d)


def single_substitutions(font, feature: str) -> dict[str, str]:
    """Glyph mapping of a GSUB feature made of single substitutions (lnum, ...)."""
    if "GSUB" not in font:
        return {}
    gsub = font["GSUB"].table
    mapping: dict[str, str] = {}
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag != feature:
            continue
        for index in record.Feature.LookupListIndex:
            lookup = gsub.LookupList.Lookup[index]
            for table in lookup.SubTable:
                if lookup.LookupType == 7:
                    table = table.ExtSubTable
                mapping.update(getattr(table, "mapping", None) or {})
    return mapping


def build_fonts(src: Path) -> None:
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    faces = {}
    for key, filename, weight in FONTS:
        font = instancer.instantiateVariableFont(TTFont(src / filename), {"wght": weight}, updateFontNames=False)
        cmap = font.getBestCmap()
        glyph_set = font.getGlyphSet()
        names = {char: cmap[ord(char)] for char in CHARSET if ord(char) in cmap}
        # Cormorant defaults to old-style figures; numbers on the cards read better lining.
        lining = single_substitutions(font, "lnum")
        for digit in "0123456789":
            if digit in names:
                names[digit] = lining.get(names[digit], names[digit])
        glyphs = {}
        for char, name in names.items():
            pen = SVGPathPen(glyph_set)
            glyph_set[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
            glyphs[char] = [glyph_set[name].width, compact_path(pen.getCommands())]
        hhea = font["hhea"]
        faces[key] = {
            "upm": font["head"].unitsPerEm,
            "ascender": hhea.ascent,
            "descender": hhea.descent,
            "cap": getattr(font["OS/2"], "sCapHeight", 0),
            "x": getattr(font["OS/2"], "sxHeight", 0),
            "glyphs": glyphs,
            "kern": kerning(font, names),
        }
        missing = sorted(set(CHARSET) - set(names))
        print(f"{key}: {len(glyphs)} glyphs, {len(faces[key]['kern'])} kern pairs, missing {''.join(missing)!r}")
    out = OUT / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    target = OUT / "glyphs.json.gz"
    with gzip.open(target, "wt", encoding="utf-8", compresslevel=9) as handle:
        json.dump(faces, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"{target.relative_to(ROOT)}  {target.stat().st_size / 1024:.1f} KB")
    for license_file in src.glob("OFL-*.txt"):
        if "ebgaramond" not in license_file.name:
            shutil.copyfile(license_file, out / license_file.name)


def build_grain() -> None:
    """A small speckle tile; cheaper to composite than an feTurbulence filter."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(2992)
    size = 160
    pixels = np.zeros((size, size), np.uint8)
    roll = rng.random((size, size))
    pixels[roll < 0.075] = 1
    pixels[roll > 0.93] = 2
    image = Image.fromarray(pixels, "P")
    image.putpalette([0, 0, 0, 255, 255, 255, 0, 0, 0] + [0, 0, 0] * 253)
    image.info["transparency"] = bytes([0, 34, 46] + [0] * 253)
    target = OUT / "grain.png"
    image.save(target, optimize=True, transparency=bytes([0, 34, 46] + [0] * 253))
    print(f"{target.relative_to(ROOT)}  {target.stat().st_size / 1024:.1f} KB")


def build_header() -> None:
    """Remove the baked tagline; the renderer draws the current one as text.

    The band under the tagline is covered with texture copied from the clean
    band right above it, feathered at the edges, so grain and cracks continue.
    """
    import cv2
    import numpy as np
    from PIL import Image

    src_path = ROOT / "assets" / "header.webp"
    src = np.array(Image.open(src_path).convert("RGB")).astype(float)
    out = src.copy()
    y0, y1, x0, x1 = 350, 414, 62, 930
    shift = 64
    alpha = np.zeros((y1 - y0, x1 - x0), float)
    alpha[6:-6, 8:-8] = 1
    alpha = cv2.GaussianBlur(alpha, (0, 0), 3.0)[..., None]
    out[y0:y1, x0:x1] = alpha * src[y0 - shift:y1 - shift, x0:x1] + (1 - alpha) * src[y0:y1, x0:x1]
    target = OUT / "header-clean.webp"
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(target, quality=90, method=6)
    print(f"{target.relative_to(ROOT)}  {target.stat().st_size / 1024:.1f} KB")

    # Outline of the torn paper strip, so the renderer can light only the paper.
    luma = out.mean(axis=2)
    raw = []
    for x in range(0, 1001, 5):
        column = np.where(luma[150:246, x] > 60)[0]
        raw.append(int(150 + column.min()) if len(column) else 241)
    # A median over neighbours drops stray bright specks above the edge.
    top = [[i * 5, int(np.median(raw[max(0, i - 2):i + 3]))] for i in range(len(raw))]
    target = OUT / "header-strip.json"
    target.write_text(json.dumps({"top": top, "bottom": 241}, separators=(",", ":")) + "\n")
    print(f"{target.relative_to(ROOT)}  {len(top)} points")


# (frame name, source screenshot, crop box in source pixels)
AUTOKEEPER_FRAMES = [
    ("title", "title.png", (0, 0, 1830, 1074)),
    ("library", "game.png", (0, 0, 1830, 1074)),
    ("map", "map.png", (0, 0, 1830, 1074)),
    ("combat", "fight.png", (0, 0, 1830, 1074)),
    ("styles", "styles.png", (0, 0, 2652, 960)),
]
FRAME_SIZE = (840, 472)


def build_autokeeper(img_dir: Path) -> None:
    from PIL import Image, ImageOps

    out = OUT / "autokeeper"
    out.mkdir(parents=True, exist_ok=True)
    for name, filename, box in AUTOKEEPER_FRAMES:
        image = Image.open(img_dir / filename).convert("RGB").crop(box)
        image = ImageOps.fit(image, FRAME_SIZE, Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        target = out / f"{name}.jpg"
        image.save(target, quality=70, optimize=True, progressive=True)
        print(f"{target.relative_to(ROOT)}  {target.stat().st_size / 1024:.1f} KB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fonts", type=Path, help="directory with the OFL variable fonts")
    parser.add_argument("--autokeeper-img", type=Path, help="autokeeper/docs/img")
    parser.add_argument("--header", action="store_true", help="rebuild assets/src/header-clean.webp")
    parser.add_argument("--grain", action="store_true", help="rebuild assets/src/grain.png")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.fonts:
        build_fonts(args.fonts)
    if args.header:
        build_header()
    if args.grain:
        build_grain()
    if args.autokeeper_img:
        build_autokeeper(args.autokeeper_img)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
