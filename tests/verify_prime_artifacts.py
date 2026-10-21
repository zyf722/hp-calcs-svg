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
    # Physical columns, not just the strings printed on individual keys:
    # the older drawing put 20 SVG units too much gap between 8 and 9.
    def key_gap(a: str, b: str) -> float:
        a_x, _, a_w, _ = (float(v) for v in nodes["key-" + a].attrib["data-hitbox"].split(","))
        b_x, _, _, _ = (float(v) for v in nodes["key-" + b].attrib["data-hitbox"].split(","))
        return b_x - (a_x + a_w)

    for sequence in (("7", "8", "9", "divide"), ("4", "5", "6", "multiply"),
                     ("1", "2", "3", "subtract"), ("0", "dot", "negate", "add")):
        gaps = [key_gap(left, right) for left, right in zip(sequence, sequence[1:])]
        assert max(gaps) - min(gaps) <= 2.0, f"Uneven Prime numeric key pitch: {sequence}, {gaps}"

    # Each key has a thin modifier-bearing front-side material treatment.
    # The principal key face must not have the failed oversized trapezoid.
    slopes = [
        node for node in root.iter(tag("rect"))
        if node.get("data-part") == "modifier-front-slope"
    ]
    assert len(slopes) == 37, f"Expected 37 shallow front facets, found {len(slopes)}"
    for facet in slopes:
        assert float(facet.attrib["height"]) <= 0.34 * 83, "Modifier facet covers the principal key face"

    for expected in ("symb-italic-x", "icon-mem", "icon-plot", "icon-num",
                     "icon-view", "icon-menu", "icon-del",
                     "units-comma-1", "units-comma-2", "root-degree"):
        assert expected in nodes, f"Missing source-photo-matched SVG detail: {expected}"

    # Verify real font-derived ink positioning on the generated deliverables:
    # x^y, x², e^x, 10^x and x^-1 are not one unshaped Unicode string.
    for base, raised in (
        ("main-power", "power-exponent"),
        ("main-square", "square-exponent"),
        ("secondary-ln", "raised-exponent-ln"),
        ("secondary-log", "raised-exponent-log"),
        ("secondary-divide", "raised-exponent-divide"),
    ):
        body, exponent = bounds(nodes[base]), bounds(nodes[raised])
        horizontal_gap = exponent[0] - body[2]
        assert -4.5 <= horizontal_gap <= 5.0, (
            f"Detached/overlapping superscript {base}: gap={horizontal_gap:.2f}"
        )
        assert exponent[1] < body[1], f"{raised} is not raised above {base}"
    # The fraction numerator must not sit on the top border of the key.
    assert bounds(nodes["fraction-num"])[1] >= 1108.0
    left, top, right, bottom = bounds(nodes["secondary-del"])
    assert abs((left + right) / 2 - 851) <= 1.5, "DEL blue legend is not centered"
    assert 1155 <= top < bottom <= 1182, "DEL legend left its sloping front"

    # Production-font visual regression: check the actually rendered glyph
    # bounds, not merely JSON strings or placeholder font metrics.
    for identifier in ("main-vars", "secondary-enter", "main-comma",
                       "abs-math-x", "comma-cross-arrows",
                       "fraction-prime", "fraction-double-prime"):
        assert identifier in nodes, f"Missing Prime engraving: {identifier}"

    for identifier in ("ln", "log", "divide"):
        x, y, width, height = (
            float(value) for value in nodes["key-" + identifier]
            .get("data-hitbox", "").split(",")
        )
        top = y + height * 0.65
        bottom = y + height * 0.94
        for glyph in ("secondary-" + identifier,
                      "raised-exponent-" + identifier):
            bx0, by0, bx1, by1 = bounds(nodes[glyph])
            assert by0 >= top - 2.0, (
                f"{glyph} starts above the grey modifier facet: {by0}/{top}"
            )
            assert by1 <= bottom + 2.0, (
                f"{glyph} extends below the grey modifier facet: {by1}/{bottom}"
            )
            assert x + 7 <= bx0 and bx1 <= x + width - 7, (
                f"{glyph} leaves the modifier's horizontal bounds"
            )

    # Font-specific checks prevent regressions to Jost or regular Noto Math
    # for Latin mathematical variables, mathematical commas, i and pi.
    if outlined:
        for identifier, expected in (
            ("main-comma", "GSI"),
            ("abs-math-x", "GSI"),
            ("secondary-2", "GSI"),
            ("secondary-3", "GSI"),
            ("root-degree", "GSI"),
            ("square-exponent", "GS"),
        ):
            fonts = {
                path.get("data-font")
                for path in nodes[identifier].iter(tag("path"))
                if path.get("data-font")
            }
            assert expected in fonts, f"{identifier} uses {fonts}, not {expected}"
    else:
        vars_text = list(nodes["main-vars"].iter(tag("text")))
        assert len(vars_text) == 1
        assert abs(float(vars_text[0].get("letter-spacing", "0")) + .8) <= .01
        for identifier in ("secondary-symb", "secondary-help", "secondary-menu"):
            text_nodes = list(nodes[identifier].iter(tag("text")))
            assert len(text_nodes) == 1
            assert float(text_nodes[0].get("font-size", "0")) >= 20, identifier
        enter_text = list(nodes["secondary-enter"].iter(tag("text")))
        assert len(enter_text) == 1
        assert float(enter_text[0].get("font-size", "0")) >= 31

    # Ensure the toolbox handle remains within the top black inlay.
    mem = nodes["icon-mem"]
    assert "scale(1.1250)" in mem.get("transform", "")

    # The blue STO inscription and dark triangle must be contiguous.
    import re
    triangles = [
        element for element in nodes["key-eex"].iter(tag("path"))
        if element.get("data-part") == "sto-triangle"
    ]
    assert len(triangles) == 1
    first_x = re.search(r"^M(-?[0-9.]+)", triangles[0].get("d", ""))
    assert first_x is not None
    assert abs(float(first_x.group(1)) - bounds(nodes["secondary-eex"])[2]) <= 1.0

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
