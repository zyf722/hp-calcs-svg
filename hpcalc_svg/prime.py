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
        brush = ET.SubElement(self.defs, svg_tag("pattern"), {
            "id": "prime-brush", "width": "9", "height": "7",
            "patternUnits": "userSpaceOnUse",
        })
        for x, color, opacity in [
            (1, "#ffffff", ".22"), (2.5, "#121920", ".12"),
            (5.1, "#ffffff", ".16"), (8.1, "#111923", ".15"),
        ]:
            ET.SubElement(brush, svg_tag("path"), {
                "d": f"M{x} 0 V7", "stroke": color,
                "stroke-width": ".5", "opacity": opacity,
            })

    def _shell(self) -> None:
        self.shell()
        panel = next(path for path in self.d["paths"] if path["id"] == "metal-panel")
        metal = self.group(self.scene, "brushed-aluminium")
        self.path(metal, panel["d"], fill="url(#prime-brush)", opacity=".58")
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
            path("M-20 -9 H20 V17 H-20 Z", fill=color)
            path("M-9 -9 V-15 H9 V-9", **line)
            path("M-20 3 H-3 M3 3 H20", fill="none",
                 stroke="#25272a", stroke_width=3)
            path("M-3 -2 H3 V9 H-3 Z", fill="none",
                 stroke="#242529", stroke_width=2.1)
        elif icon == "del":
            path("M-24 0 L-8 -15 H20 V15 H-8 Z", fill="#292c31")
            path("M-6 -8 L9 8 M9 -8 L-6 8", **line)
        elif icon == "symb":
            path("M-13 -12 H13 V12 H-13 Z M-7 -6 L7 6 M7 -6 L-7 6", **line)
        elif icon == "plot":
            path("M-17 13 V-14 M-17 13 H17 M-11 3 L-2 -2 L7 5 L15 -10", **line)
        elif icon == "num":
            path("M-17 -15 H17 V15 H-17 Z M-17 -5 H17 M-17 5 H17 "
                 "M-5 -15 V15 M6 -15 V15", **line)
        elif icon == "help":
            path("M-17 -14 H17 V14 H-17 Z", fill="#d6d9de")
            self._label(k, "question", "?", 0, 0, "#272a2e", 27, "JS")
        elif icon == "view":
            path("M-18 -13 H9 V7 H-18 Z M-8 -5 H18 V15 H-8 Z", **line)
        elif icon == "menu":
            for y in (-11, 0, 11):
                path(f"M-16 {y} H-10", fill="none", stroke=color,
                     stroke_width=4, stroke_linecap="round")
                path(f"M-4 {y} H18", fill="none", stroke=color,
                     stroke_width=3, stroke_linecap="round")

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
        self.path(g, f"M{x+5} {y+3} H{x+w-5}", fill="none",
                  stroke="#ffffff", stroke_width=1.15, opacity=".9")
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
                       53 if icon == "mem" else 43)
        else:
            primary_color = "#fafaf9" if cap else self.d["palette"]["primary_text"]
            label = key["label"]
            if label:
                self._label(g, "main-" + key["id"], label,
                            cx-5 if key["id"] == "power" else cx,
                            cy-16, primary_color,
                            key.get("main_size", row["default_size"]),
                            key.get("main_font", "JS"), role="primary")
        kid = key["id"]
        if kid == "square":
            self._label(g, "square-exponent", "2", cx+17, cy-37,
                        "#272731", 24, "JM", role="primary")
        elif kid == "power":
            self._label(g, "power-exponent", "y", cx+19, cy-33,
                        "#272731", 20, "GSI", role="primary")
        elif kid == "units":
            for rx, ry, side in [
                (cx-30, cy-17, 16), (cx+9, cy-17, 14), (cx+33, cy-17, 15),
            ]:
                self.rect(g, rx-side/2, ry-side/2, side, side, 0,
                          fill="none", stroke="#34353a", stroke_width=1.2,
                          stroke_dasharray="3,2")
        elif kid == "dot":
            self.circle(g, cx, cy-17, 5.8, fill="#292a30")
        elif kid == "negate":
            self.path(g, f"M{cx-21} {cy-21} V{cy-13} H{cx+21} V{cy-21}",
                      fill="none", stroke="#272731", stroke_width=4.3,
                      stroke_linejoin="round", stroke_linecap="square")
        elif kid == "parentheses":
            self.rect(g, x+12, cy+18, 16, 14, 0,
                      fill="none", stroke="#005092", stroke_width=1.4,
                      stroke_dasharray="3,2")
        secondary = key.get("secondary")
        if secondary:
            font = key.get("secondary_font", "JM")
            centered = key.get("secondary_center", False)
            self._label(g, "secondary-" + key["id"], secondary,
                        cx if centered else x+10, cy+26,
                        self.d["palette"]["legend_blue"],
                        23 if len(secondary)<7 else 21, font,
                        "center" if centered else "left", "shift-legend")
        blue = self.d["palette"]["legend_blue"]
        if kid == "power":
            self._label(g, "root-degree", "n", x+10, cy+15,
                        blue, 14, "JM", "left")
        elif kid in ("ln", "log", "divide"):
            x_start = x+10+(14 if kid == "ln" else 29 if kid == "log" else 12)
            self._label(g, "raised-exponent-" + kid,
                        "x" if kid != "divide" else "-1",
                        x_start, cy+17, blue, 15,
                        "NM" if kid == "divide" else "JM", "left")
        elif kid == "eex":
            self.path(g, f"M{x+57} {cy+20} l10 6 -10 6 Z", fill=blue)
        elif kid == "fraction":
            self.circle(g, x+11, cy+21, 3.2, fill="none",
                        stroke=blue, stroke_width=1.4)
        if key.get("alpha"):
            self._label(g, "alpha-" + key["id"], key["alpha"], x+w-10, cy+26,
                        self.d["palette"]["legend_orange"], 23,
                        "JS", "right", "alpha-legend")

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
