"""Check generated HP Prime editable and outlined SVG files.

Run after the build, so glyph bounds reflect the exact CI fonts.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

NS = "http://www.w3.org/2000/svg"


def tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def bounds(node: ET.Element) -> tuple[float, ...]:
    value = node.get("data-bbox")
    assert value is not None, f"Missing glyph ink bounds on {node.get('id')}"
    box = tuple(float(s) for s in value.split(","))
    assert len(box) == 4 and all(math.isfinite(x) for x in box)
    return box


def check(path: Path, outlined: bool) -> None:
    root = ET.parse(path).getroot()
    assert root.tag == tag("svg") and root.get("viewBox") == "0 0 1023 2048"
    assert root.get("role") == "img"
    ids = [node.get("id") for node in root.iter() if node.get("id")]
    assert len(ids) == len(set(ids)), "Duplicate element ids"
    nodes = {node.get("id"): node for node in root.iter() if node.get("id")}
    keys = {name: node for name, node in nodes.items() if name.startswith("key-")}
    assert len(keys) == 47, f"Expected 47 keys, got {len(keys)}"
    assert nodes["touchscreen"].get("data-native-pixels") == "320x240"
    for name in ("brushed-aluminium", "navigation", "units-symbols",
                 "fraction-whole", "fraction-num", "fraction-den"):
        assert name in nodes, f"Missing vector layer: {name}"
    assert not list(root.iter(tag("image"))), "Embedded raster image"
    assert not list(root.iter(tag("foreignObject"))), "Nonportable foreignObject"
    if outlined:
        assert not list(root.iter(tag("text"))), "Unoutlined text"
    else:
        assert list(root.iter(tag("text"))), "Editable text missing"

    for name, node in keys.items():
        x, y, width, height = (float(s) for s in node.attrib["data-hitbox"].split(","))
        assert 90 <= x and x + width <= 920 and 805 <= y and y + height <= 1870, name
        shift = nodes.get(name.replace("key-", "secondary-", 1))
        alpha = nodes.get(name.replace("key-", "alpha-", 1))
        if shift is not None and alpha is not None:
            shift_ink, alpha_ink = bounds(shift), bounds(alpha)
            assert shift_ink[2] + 2 <= alpha_ink[0], (
                f"Colliding shift and alpha legends on {name}: "
                f"{shift_ink} / {alpha_ink}"
            )
    for node in root.iter():
        if node.get("data-bbox") is not None:
            bounds(node)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/verify_prime_artifacts.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    check(out / "HPPrime_editable.svg", False)
    check(out / "HPPrime_outlined.svg", True)
    with Image.open(out / "HPPrime_preview.png") as png:
        assert abs(png.width - 1023 * 1.5) <= .5
        assert abs(png.height - 2048 * 1.5) <= .5
    print("PASS: HP Prime SVG vectors, 47 keys, glyph ink separation, preview")


if __name__ == "__main__":
    main()
