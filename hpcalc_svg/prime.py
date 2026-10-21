"""Dedicated, data-driven SVG renderer for the HP Prime front panel.

The Prime's touch display, circular navigation pad and two-material keypad do
not share the earlier 39g+/49g+ chassis geometry. The key coordinates, legends,
finishes and body paths are kept in design/hpprime.json, not in a compiled SVG.
"""

from __future__ import annotations

import math
from typing import Any
from xml.etree import ElementTree as ET

from hpcalc_svg.renderer import Renderer, svg_tag


class PrimeRenderer(Renderer):
    """Reuse the common vector text/outlined-glyph pipeline for HP Prime."""

    def _label(
        self, parent: ET.Element, name: str, label: str, x: float, y: float,
        color: str, size: float, font: str = "JM",
        align: str = "center", role: str = "legend",
    ) -> None:
        if label:
            self.text(parent, name, self.parts(label, font, size), color, align, x, y, role)

    def _extra_defs(self) -> None:
        metal = next(item for item in self.defs if item.get("id") == "prime-metal")
        metal.set("x2", "1")
        metal.set("y2", "0")
        radial = ET.SubElement(self.defs, svg_tag("radialGradient"), {
            "id": "prime-nav-face", "cx": "45%", "cy": "39%", "r": "70%",
        })
        for offset, color in [("0", "#3b3d42"), (".65", "#24262a"), ("1", "#101217")]:
            ET.SubElement(radial, svg_tag("stop"), {"offset": offset, "stop-color": color})
        # The modifier markings belong to the shallow *front sloping side* of
        # each keycap. This is a lighting gradient, not an inset trapezoid
        # printed onto the top face.
        slope = ET.SubElement(self.defs, svg_tag("linearGradient"), {
            "id": "prime-key-front-slope", "x1": "0", "y1": "0",
            "x2": "0", "y2": "1",
        })
        for offset, color in [
            ("0", "#dedbd6"), (".22", "#f2f0ed"),
            (".70", "#f8f7f4"), ("1", "#dedbd7"),
        ]:
            ET.SubElement(slope, svg_tag("stop"), {
                "offset": offset, "stop-color": color,
            })
        brush = ET.SubElement(self.defs, svg_tag("pattern"), {
            "id": "prime-brush", "width": "13", "height": "9",
            "patternUnits": "userSpaceOnUse",
        })
        for x, color, opacity in [
            (1.1, "#ffffff", ".17"), (3.4, "#121920", ".09"),
            (7.6, "#ffffff", ".13"), (11.2, "#111923", ".1"),
        ]:
            ET.SubElement(brush, svg_tag("path"), {
                "d": f"M{x} 0 V9", "stroke": color,
                "stroke-width": ".35", "opacity": opacity,
            })

    def _shell(self) -> None:
        self.shell()
        panel = next(path for path in self.d["paths"] if path["id"] == "metal-panel")
        metal = self.group(self.scene, "brushed-aluminium")
        self.path(metal, panel["d"], fill="url(#prime-brush)", opacity=".48")
        self.path(metal, "M56 1080 H967", fill="none", stroke="#f0edeb",
                  stroke_width=1.1, opacity=".67")

    def _display(self) -> None:
        d = self.d["display"]
        g = self.group(self.scene, "touchscreen", data_native_pixels="320x240")
        x, y, w, h, _ = d["screen"]
        self.rect(g, x-4, y-4, w+8, h+8, 0,
                  fill="#111113", stroke="#353434", stroke_width=1.3)
        self.rect(g, x, y, w, h, 0, fill=d["screen_fill"],
                  stroke=d["screen_stroke"], stroke_width=d["screen_stroke_width"])
        self.path(g, f"M{x+1} {y+1} H{x+w-1}", fill="none",
                  stroke="#292727", stroke_width=1.15, opacity=".66")
        self.path(g, f"M{x+2} {y+h-2} H{x+w-2}", fill="none",
                  stroke="#0c0c0d", stroke_width=1.5, opacity=".58")

    def _logo(self) -> None:
        d = self.d["logo"]
        g = self.group(self.scene, "prime-hp-logo", data_source=d["source_page"])
        cx, cy, radius = d["circle"]
        self.circle(g, cx, cy, radius, fill="#17191c")
        source = ET.parse(self.project_root / d["asset"]).getroot()
        source_group = next((node for node in source if node.tag.endswith("g")), None)
        source_path = next((node for node in source.iter() if node.tag.endswith("path")), None)
        if source_path is None or not source_path.get("d"):
            raise ValueError("HP logo source SVG has no path geometry")
        x, y, w, h = d["svg"]
        mark = ET.SubElement(g, svg_tag("svg"), {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "viewBox": "0 0 1000 999.98", "overflow": "visible",
        })
        transform = source_group.get("transform") if source_group is not None else None
        target = ET.SubElement(mark, svg_tag("g"), {"transform": transform}) if transform else mark
        self.path(target, source_path.get("d") or "", fill="#d3cbc0")

    def _header(self) -> None:
        h = self.d["header"]
        g = self.group(self.scene, "header-print")
        self._label(g, "model-title", h["brand_text"], h["x"], h["top_y"],
                    h["text_color"], h["font_size"], "JB", "top-left", "header")

    def _navigation(self) -> None:
        n = self.d["nav"]
        cx, cy, r = n["cx"], n["cy"], n["outer_radius"]
        g = self.group(self.scene, "navigation", data_center=f"{cx},{cy}")
        self.circle(g, cx, cy+3, r+7, fill="#08090b", opacity=".64")
        self.circle(g, cx, cy, r+3, fill="#0e1014", stroke="#060709", stroke_width=2)
        self.circle(g, cx, cy, r-6, fill="#303239", stroke="#53555a", stroke_width=1.2)
        self.circle(g, cx, cy, n["inner_radius"]+5, fill="#0d0e10",
                    stroke="#16181b", stroke_width=5)
        self.circle(g, cx, cy, n["inner_radius"], fill="url(#prime-nav-face)",
                    stroke="#424348", stroke_width=1.1)
        # Four low-contrast machining sectors evoke the physical brushed dial.
        for start_deg, end_deg, tone, alpha in [
            (-135, -45, "#aaaaaf", .085),
            (-45, 45, "#050507", .115),
            (45, 135, "#a0a1a7", .065),
            (135, 225, "#07090b", .085),
        ]:
            radius = n["inner_radius"] - 3
            a0, a1 = math.radians(start_deg), math.radians(end_deg)
            x0, y0 = cx+radius*math.cos(a0), cy+radius*math.sin(a0)
            x1, y1 = cx+radius*math.cos(a1), cy+radius*math.sin(a1)
            self.path(g, f"M{cx} {cy} L{x0:.3f} {y0:.3f} "
                         f"A{radius} {radius} 0 0 1 {x1:.3f} {y1:.3f} Z",
                      fill=tone, opacity=alpha)
        # Radial engraving is made of editable paths, not a raster texture.
        for deg in range(0, 360, 6):
            angle = math.radians(deg)
            r0, r1 = 14, n["inner_radius"]-5
            self.path(g, (f"M{cx+math.cos(angle)*r0:.3f} {cy+math.sin(angle)*r0:.3f} "
                          f"L{cx+math.cos(angle)*r1:.3f} {cy+math.sin(angle)*r1:.3f}"),
                      fill="none", stroke="#a4a8b2", stroke_width=".48", opacity=".048")
        for dx, dy, vx, vy in [
            (0, -70, 0, -17), (0, 70, 0, 17),
            (-70, 0, -17, 0), (70, 0, 17, 0),
        ]:
            self.path(g, f"M{cx+dx-vx*.37} {cy+dy-vy*.37} "
                         f"L{cx+dx+vx*.37} {cy+dy+vy*.37}",
                      fill="none", stroke="#08090c", stroke_width=2.2,
                      stroke_linecap="round", opacity=".78")
        self.path(g, f"M{cx-63} {cy-70} A96 96 0 0 1 {cx+36} {cy-86}",
                  fill="none", stroke="#8b8b91", stroke_width=3,
                  opacity=".25", stroke_linecap="round")

    def _icon(
        self, group: ET.Element, icon: str, cx: float, cy: float,
        color: str, width: float = 37,
    ) -> None:
        k = self.group(group, f"icon-{icon}",
                       transform=f"translate({cx} {cy}) scale({width/40:.4f})")

        def path(d: str, **style: object) -> None:
            self.path(k, d, **style)

        line: dict[str, object] = {
            "fill": "none", "stroke": color, "stroke_width": 3.1,
            "stroke_linejoin": "round", "stroke_linecap": "round",
        }
        if icon == "home":
            path("M-20 -1 L0 -21 L20 -1 H13 V18 H3 V5 H-5 V18 H-14 V-1 Z", **line)
        elif icon == "mem":
            # White briefcase with shoulder, handle and negative-space clasp.
            # Built from editable silhouette geometry, not a generic suitcase.
            path("M-23 -6 L-17 -13 H17 L23 -6 V17 H-23 Z", fill=color)
            path("M-9 -13 V-19 H9 V-13", **line)
            path("M-22 1 H-4 M4 1 H22", fill="none",
                 stroke="#25272a", stroke_width=2.3)
            path("M-4 -4 H4 V8 H-4 Z", fill="#292a2d")
            path("M-2 -2 H2 V6 H-2 Z", fill="#f2f2f1")
        elif icon == "del":
            # Solid left-pointing backspace arrow with white cut-out X.
            path("M-25 0 L-11 -14 H21 Q23 -14 23 -11 V11 Q23 14 21 14 H-11 Z",
                 fill="#2b2d30")
            path("M-4 -8 L9 8 M9 -8 L-4 8", fill="none",
                 stroke="#f7f7f5", stroke_width=4.0, stroke_linecap="round")
        elif icon == "symb":
            # Real key shows a small pale rounded square with an italic 'x',
            # not the crossed-box/delete icon used in the first draft.
            self.rect(k, -15, -15, 30, 30, 5, fill="#e3e4e7")
            self._label(k, "symb-italic-x", "x", 0, -1,
                        "#282a2e", 25, "GSI", role="key-icon")
        elif icon == "plot":
            # Coordinate axes with arrowheads and a smooth graph trace.
            path("M-18 12 V-18 M-21 -13 L-18 -18 L-15 -13 "
                 "M-18 12 H19 M14 9 L19 12 L14 15", **line)
            path("M-12 6 C-7 5 -5 -2 0 -7 S8 -6 12 -10 L16 -14",
                 fill="none", stroke=color, stroke_width=3.1,
                 stroke_linecap="round")
        elif icon == "num":
            # Two-column table with ruled horizontal entries.
            path("M-18 -17 H18 V17 H-18 Z M-18 -6 H18 M-18 6 H18 "
                 "M1 -17 V17", **line)
            path("M-15 -11 H-2 M5 -11 H15 M-15 0 H-2 M5 0 H15 "
                 "M-15 12 H-2 M5 12 H15", fill="none",
                 stroke=color, stroke_width=1.6)
        elif icon == "help":
            path("M-17 -14 H17 V14 H-17 Z", fill="#d6d9de")
            self._label(k, "question", "?", 0, 0, "#272a2e", 27, "JS")
        elif icon == "view":
            path("M-19 -14 H9 V7 H-19 Z M-9 -5 H19 V16 H-9 Z", **line)
            path("M-5 -1 H15 V12 H-5 Z", fill="#e5e7e9")
        elif icon == "menu":
            for y in (-12, 0, 12):
                self.rect(k, -18, y-3, 7, 7, 1.3, fill=color)
                self.rect(k, -6, y-2.5, 25, 5, 1.3, fill=color)

    def _dark_key(
        self, parent: ET.Element, key: dict[str, Any], row: dict[str, Any],
    ) -> None:
        cx, cy = float(key["cx"]), float(key.get("center_y", row["center_y"]))
        w, h = float(key["width"]), float(key.get("height", row["height"]))
        g = self.group(parent, "key-" + key["id"], data_center=f"{cx:g},{cy:g}",
                       data_hitbox=f"{cx-w/2:.1f},{cy-h/2:.1f},{w:.1f},{h:.1f}")
        self.rect(g, cx-w/2-5, cy-h/2-7, w+10, h+13, 8,
                  fill="#07080a", stroke="#161719", stroke_width=3)
        self.rect(g, cx-w/2, cy-h/2, w, h, 5,
                  fill="url(#prime-dark-key)", stroke="#4b4c4f", stroke_width=1.2)
        self.path(g, f"M{cx-w/2+5} {cy-h/2+2} H{cx+w/2-5}",
                  fill="none", stroke="#757478", stroke_width=.7, opacity=".38")
        icon = key.get("icon")
        if icon == "home":
            self._icon(g, icon, cx, cy-12, "#e5e7e9", 40)
        else:
            shift = 13 if icon in ("help", "view", "menu") else (
                -13 if icon in ("symb", "plot", "num") else 0
            )
            self._label(g, "main-" + key["id"], key["label"], cx+shift, cy-12,
                        "#e6e7ec", key.get("main_size", row["default_size"]), "JM")
            if icon:
                dx = -37 if icon in ("help", "view", "menu") else 35
                self._icon(g, icon, cx+dx, cy-12, "#d7e0e5", 24)
        secondary = key.get("secondary", "")
        if secondary == "Setup":
            self.path(g, f"M{cx-33} {cy+22} v-7 m0 7 h12 l-4 -4 m4 4 l-4 4",
                      fill="none", stroke="#70b7d4", stroke_width=1.9,
                      stroke_linecap="round", stroke_linejoin="round")
            self._label(g, "secondary-" + key["id"], "Setup",
                        cx+13, cy+21, "#70b7d4", 17.5)
        elif secondary:
            self._label(g, "secondary-" + key["id"], secondary,
                        cx, cy+23, "#72bad6", 20)

    def _light_key(
        self, parent: ET.Element, key: dict[str, Any], row: dict[str, Any],
    ) -> None:
        cx, cy = float(key["cx"]), float(row["center_y"])
        w, h = float(key["width"]), float(row["height"])
        x, y = cx-w/2, cy-h/2
        g = self.group(parent, "key-" + key["id"], data_center=f"{cx:g},{cy:g}",
                       data_hitbox=f"{x:.1f},{y:.1f},{w:.1f},{h:.1f}")
        self.rect(g, x-3, y-4, w+6, h+6, 7,
                  fill="#090a0c", stroke="#171819", stroke_width=1.5)
        self.rect(g, x+1.6, y+1.2, w-3.2, h-3.1, 4.8,
                  fill="url(#prime-light-key)", stroke="#aaa9a9", stroke_width=1.15)
        profile = self.d["keyboard"]["light_key_profile"]
        front_y = y + h * profile["front_slope_start_ratio"]
        front_h = h * (profile["front_slope_end_ratio"] - profile["front_slope_start_ratio"])
        # A front-elevation view of a side-profile trapezoidal key: only the
        # lower modifier-bearing side gets a shallow planar change of lighting.
        # No polygon is added across the principal top face.
        self.rect(g, x+3.7, front_y, w-7.4, front_h, 1.0,
                  fill="url(#prime-key-front-slope)",
                  opacity=profile["front_facade_opacity"])
        # Thin lateral chamfers, not a second trapezoid on the key face.
        self.path(g, f"M{x+3.2} {y+5} V{y+h-7}", fill="none",
                  stroke="#ffffff", stroke_width=profile["left_bevel_width"],
                  opacity=".27")
        self.path(g, f"M{x+w-3.2} {y+5} V{y+h-7}", fill="none",
                  stroke="#373737", stroke_width=profile["right_bevel_width"],
                  opacity=".10")
        self.path(g, f"M{x+5} {y+3} H{x+w-5}", fill="none",
                  stroke="#ffffff", stroke_width=1.15,
                  opacity=profile["top_edge_highlight_opacity"])
        self.path(g, f"M{x+5} {front_y+.7} H{x+w-5}", fill="none",
                  stroke="#a9a8a4", stroke_width=.75, opacity=".15")
        self.path(g, f"M{x+5} {y+h-5} H{x+w-5}", fill="none",
                  stroke="#777b80", stroke_width=1.5, opacity=".28")
        for fraction in (.16, .84):
            notch_x = x+w*fraction
            self.rect(g, notch_x-5.5, y-4.5, 11, 4.3, 0, fill="#121215")
        cap = key.get("cap")
        if cap:
            cap_color = "url(#prime-orange)" if cap == "orange" else "url(#prime-blue)"
            self.rect(g, x+4, y+4, w-8, h*.53, 3.5, fill=cap_color)
        if key.get("icon"):
            icon = key["icon"]
            if icon == "mem":
                self.rect(g, x+4, y+4, w-8, h*.52, 2.5, fill="#26272b")
            self._icon(g, icon, cx, cy-16, "#f7f7f5",
                       54 if icon == "mem" else 49 if icon == "del" else 43)
        else:
            primary_color = "#fafaf9" if cap else self.d["palette"]["primary_text"]
            label = key["label"]
            if label and key["id"] not in ("units", "fraction", "define"):
                self._label(g, "main-" + key["id"], label,
                            cx-5 if key["id"] == "power" else cx,
                            cy-16, primary_color,
                            key.get("main_size", row["default_size"]),
                            key.get("main_font", "JS"), role="primary")
        kid = key["id"]
        if kid == "square":
            # Font-derived superscript; position relative to the x's actual
            # ink center rather than treating "x²" as one unshaped text string.
            self._label(g, "square-exponent", "2", cx+17, cy-27,
                        "#272731", 22, "JM", role="primary")
        elif kid == "power":
            self._label(g, "power-exponent", "y", cx+19, cy-27,
                        "#272731", 20, "GSI", role="primary")
        elif kid == "define":
            # Separate optically spaced italic variables, including theta.
            for name, char, dx, size, font in (
                ("x", "x", -30, 26.0, "GSI"),
                ("t", "t", -10, 25.5, "GSI"),
                ("theta", "θ", 10, 27.0, "GSI"),
                ("n", "n", 31, 26.0, "GSI"),
            ):
                self._label(g, "define-" + name, char, cx+dx, cy-16,
                            "#272731", size, font, role="primary")
        elif kid == "units":
            # The reference is a fraction of dotted placeholders, a radical
            # containing a dotted placeholder, and a barred placeholder.
            # A generic 2x2 matrix (as in earlier builds) is incorrect.
            icons = self.group(g, "units-symbols", fill="none",
                               stroke="#34353a", stroke_width=1.7)
            for oy in (cy-34, cy-11):
                self.rect(icons, cx-41, oy, 15, 17, 0, fill="none",
                          stroke_width=1.55, stroke_dasharray="3.2,2.1")
            self.path(icons, f"M{cx-43} {cy-14} H{cx-24}",
                      fill="none", stroke_width=1.7)
            # A dark comma separates the miniature math fields.
            self._label(g, "units-comma-1", ",", cx-19, cy-12,
                        "#34353a", 23, "GSI", role="primary")
            self.path(icons, f"M{cx-11} {cy-19} l6 9 8 -24 h21",
                      fill="none", stroke_width=2.5,
                      stroke_linejoin="round")
            self.rect(icons, cx+9, cy-24, 13, 17, 0, fill="none",
                      stroke_width=1.4, stroke_dasharray="2.7,1.7")
            self._label(g, "units-comma-2", ",", cx+27, cy-12,
                        "#34353a", 23, "GSI", role="primary")
            self.path(icons, f"M{cx+35} {cy-34} V{cy-7} "
                             f"M{cx+54} {cy-34} V{cy-7}",
                      fill="none", stroke_width=2.6)
            self.rect(icons, cx+39, cy-26, 12, 16, 0, fill="none",
                      stroke_width=1.5, stroke_dasharray="2.4,1.6")
        elif kid == "fraction":
            # Compose the numerator, slash and denominator as separate glyphs.
            ink = self.d["palette"]["primary_text"]
            self._label(g, "fraction-whole", "a", cx-31, cy-16, ink, 34,
                        "GSI", role="primary")
            self._label(g, "fraction-num", "b", cx+2, cy-29, ink, 26,
                        "GSI", role="primary")
            self._label(g, "fraction-den", "c", cx+25, cy-7, ink, 25,
                        "GSI", role="primary")
            self.path(g, f"M{cx+17} {cy-34} l-11 30", fill="none",
                      stroke=ink, stroke_width=2.3)
        elif kid == "dot":
            self.circle(g, cx, cy-17, 5.8, fill="#292a30")
        elif kid == "negate":
            self.path(g, f"M{cx-21} {cy-21} V{cy-13} H{cx+21} V{cy-21}",
                      fill="none", stroke="#272731", stroke_width=4.3,
                      stroke_linejoin="round", stroke_linecap="square")
        elif kid == "parentheses":
            # Dotted placeholder with surrounding printer-like prime marks.
            self.rect(g, x+16, cy+19, 15, 12, 0,
                      fill="none", stroke="#005092", stroke_width=1.35,
                      stroke_dasharray="2.4,1.8")
            self.path(g, f"M{x+10} {cy+13} v7 m-3 -4 v5 M{x+35} {cy+13} v7",
                      fill="none", stroke="#005092", stroke_width=1.7)
        elif kid == "comma":
            # Expand/contract symbol alongside the printed comma, missing
            # from the original approximate SVG.
            tx, ty = cx+32, cy-19
            self.path(g, f"M{tx-9} {ty+8} L{tx} {ty-1} H{tx-5} "
                         f"M{tx} {ty-1} V{ty+4} "
                         f"M{tx+8} {ty-7} L{tx+1} {ty} H{tx+6} "
                         f"M{tx+1} {ty} V{ty-5}",
                      fill="none", stroke="#2b2c31", stroke_width=1.8,
                      stroke_linecap="round", stroke_linejoin="round")
        secondary = key.get("secondary")
        if secondary and kid not in ("ln", "log", "divide"):
            font = key.get("secondary_font", "JM")
            centered = key.get("secondary_center", False) or kid == "del"
            secondary_size = 23.0 if len(secondary) < 7 else 21.0
            if not centered and key.get("alpha"):
                # Keep shift ink out of the reserved right-hand ALPHA letter lane.
                alpha_width = self.ink_width(self.parts(key["alpha"], "JS", 23))
                available = w - 26 - alpha_width - 9
                while secondary_size > 14 and self.ink_width(
                    self.parts(secondary, font, secondary_size)
                ) > available:
                    secondary_size -= .5
            self._label(g, "secondary-" + key["id"], secondary,
                        cx if centered else x+10, cy+26,
                        self.d["palette"]["legend_blue"], secondary_size,
                        font, "center" if centered else "left", "shift-legend")
        blue = self.d["palette"]["legend_blue"]
        if kid == "power":
            self._label(g, "root-degree", "n", x+11, cy+13,
                        blue, 13, "JM", "left")
            # Native √ in the math font is overdrawn with a connected bar.
            self.path(g, f"M{x+27} {cy+17} H{x+49}",
                      fill="none", stroke=blue, stroke_width=1.4)
        elif kid == "square":
            self.path(g, f"M{x+27} {cy+18} H{x+48}",
                      fill="none", stroke=blue, stroke_width=1.4)
        elif kid in ("ln", "log", "divide"):
            # Three composite superscript typesets with distinct baselines.
            # The glyphs are still emitted by the production font outliner.
            if kid == "ln":
                base, exp, font = "e", "x", "GSI"
                offset, size = 30, 15
            elif kid == "log":
                base, exp, font = "10", "x", "JM"
                offset, size = 36, 15
            else:
                base, exp, font = "x", "−1", "GSI"
                offset, size = 30, 14
            self._label(g, "secondary-" + kid, base,
                        x+10, cy+26, blue, 23, font, "left", "shift-legend")
            self._label(g, "raised-exponent-" + kid, exp,
                        x+offset, cy+14, blue, size,
                        "NM" if kid == "divide" else "GSI",
                        "left", "shift-exponent")
        elif kid == "eex":
            self.path(g, f"M{x+57} {cy+20} l10 6 -10 6 Z", fill=blue)
        elif kid == "fraction":
            self.circle(g, x+11, cy+21, 3.2, fill="none",
                        stroke=blue, stroke_width=1.4)
        if key.get("alpha"):
            self._label(g, "alpha-" + key["id"], key["alpha"], x+w-10, cy+26,
                        self.d["palette"]["legend_orange"], 23,
                        "JS", "right", "alpha-legend")
            if secondary and not key.get("secondary_center"):
                shift_ink = self.bounds["secondary-" + key["id"]]
                alpha_ink = self.bounds["alpha-" + key["id"]]
                if shift_ink[2] + 2 > alpha_ink[0]:
                    raise ValueError(f"Crowded HP Prime shift/alpha legends: {key['id']}")

    def _keys(self) -> None:
        top = self.group(self.scene, "upper-keyboard")
        lower = self.group(self.scene, "metal-keyboard")
        seen: set[str] = set()
        boxes: list[tuple[str, float, float, float, float]] = []
        for row in self.d["keyboard"]["rows"]:
            for key in row["keys"]:
                kid = key["id"]
                if kid in seen:
                    raise ValueError(f"Duplicate HP Prime key id: {kid}")
                seen.add(kid)
                cx, cy = float(key["cx"]), float(key.get("center_y", row["center_y"]))
                w, h = float(key["width"]), float(key.get("height", row["height"]))
                boxes.append((kid, cx-w/2, cy-h/2, cx+w/2, cy+h/2))
                if key["kind"] == "dark":
                    self._dark_key(top, key, row)
                elif key["kind"] == "light":
                    self._light_key(lower, key, row)
                else:
                    raise ValueError(f"Unknown HP Prime key kind: {key['kind']}")
        for i, (id_a, ax0, ay0, ax1, ay1) in enumerate(boxes):
            for id_b, bx0, by0, bx1, by1 in boxes[i+1:]:
                if min(ax1, bx1)-max(ax0, bx0)>1 and min(ay1, by1)-max(ay0, by0)>1:
                    raise ValueError(f"Overlapping HP Prime keys: {id_a} / {id_b}")
        if len(seen) != 47:
            raise ValueError(f"Expected 47 HP Prime keys, got {len(seen)}")

    def build(self) -> ET.Element:
        self.gradients()
        self._extra_defs()
        self._shell()
        self._display()
        self._logo()
        self._header()
        self._navigation()
        self._keys()
        ids = [element.get("id") for element in self.root.iter() if element.get("id")]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate HP Prime SVG element ids")
        return self.root
