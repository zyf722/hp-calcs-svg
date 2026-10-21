"""Regression checks for the HP Prime source drawing and keyboard geometry."""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from hpcalc_svg.loader import load_design

ROOT = Path(__file__).resolve().parents[1]


class HPPrimeDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = load_design(ROOT / "design/hpprime.json")

    def test_native_display_geometry(self) -> None:
        metadata = self.design["metadata"]
        self.assertEqual(metadata["model_id"], "hpprime")
        self.assertEqual(metadata["native_lcd_pixels"], [320, 240])
        self.assertEqual(metadata["canvas"], [1023, 2048])
        x, y, width, height, radius = self.design["display"]["screen"]
        self.assertEqual(radius, 0)
        self.assertTrue(0 < x < 200 and 0 < y < 200)
        self.assertLess(abs(width / height - 4 / 3), 0.02)

    def test_keyboard_layout_and_labels(self) -> None:
        rows = self.design["keyboard"]["rows"]
        self.assertEqual(len(rows), 10)
        keys: list[dict[str, Any]] = [key for row in rows for key in row["keys"]]
        self.assertEqual(len(keys), 47)
        self.assertEqual(len({key["id"] for key in keys}), 47)
        self.assertEqual(sum(key["kind"] == "dark" for key in keys), 10)
        self.assertEqual(sum(key["kind"] == "light" for key in keys), 37)
        self.assertEqual({key["id"] for key in keys if key.get("cap")},
                         {"alpha", "shift"})
        self.assertEqual(next(key for key in keys if key["id"] == "enter")["width"], 246)
        for name in ("symb", "plot", "num", "help", "view", "menu",
                     "cas", "apps", "on", "del", "negate"):
            self.assertIn(name, {key["id"] for key in keys})
        for key in keys:
            self.assertTrue(key["label"] or key.get("icon") or
                            key["id"] in {"dot", "negate", "parentheses"})

    def test_keycaps_do_not_overlap(self) -> None:
        bounds: list[tuple[str, float, float, float, float]] = []
        for row in self.design["keyboard"]["rows"]:
            for key in row["keys"]:
                cx, cy = float(key["cx"]), float(key.get("center_y", row["center_y"]))
                w, h = float(key["width"]), float(key.get("height", row["height"]))
                x0, y0, x1, y1 = cx-w/2, cy-h/2, cx+w/2, cy+h/2
                self.assertGreaterEqual(x0, 95, key["id"])
                self.assertLessEqual(x1, 910, key["id"])
                self.assertGreaterEqual(y0, 810, key["id"])
                self.assertLessEqual(y1, 1860, key["id"])
                bounds.append((key["id"], x0, y0, x1, y1))
        for index, (first, x0, y0, x1, y1) in enumerate(bounds):
            for second, bx0, by0, bx1, by1 in bounds[index+1:]:
                self.assertFalse(min(x1, bx1)-max(x0, bx0)>1 and
                                 min(y1, by1)-max(y0, by0)>1,
                                 f"{first} overlaps {second}")

    def test_important_source_parts_are_vectors(self) -> None:
        path_ids = {path["id"] for path in self.design["paths"]}
        self.assertTrue({"metal-panel", "outer-shell", "upper-panel",
                         "display-bottom-seam"}.issubset(path_ids))
        self.assertEqual(self.design["logo"]["asset"],
                         "third_party/wikimedia/HP_logo_2008.svg")
        self.assertTrue((ROOT / self.design["logo"]["asset"]).is_file())


if __name__ == "__main__":
    unittest.main()
