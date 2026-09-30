from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import ImageFont


@dataclass(frozen=True)
class Component:
    text: str
    font: str = 'JS'
    size: float = 16.0
    dx: float = 0.0
    dy: float = 0.0
    tracking: float = -0.14
    vinculum_units: float = 0.0


class Font:
    def __init__(self, key: str, contents: bytes, family: str, weight: int, style: str) -> None:
        self.key, self.family, self.weight, self.style = key, family, weight, style
        self.raw = contents
        self.tt = TTFont(io.BytesIO(contents))
        self.cmap: dict[int, str] = self.tt.getBestCmap() or {}
        self.glyph_set: Any = self.tt.getGlyphSet()
        self.upm = self.tt['head'].unitsPerEm
        self.metric: Any = ImageFont.truetype(io.BytesIO(contents), 1000)
        self.paths: dict[str, tuple[str, Any]] = {}

    def name(self, char: str) -> str:
        glyph = self.cmap.get(ord(char))
        if glyph is None:
            raise ValueError(f'{self.key} has no U+{ord(char):04X} ({char!r})')
        if char == 'a' and self.family == 'Jost*':
            return 'a.alt'
        return glyph

    def glyph(self, char: str, vinculum_units: float = 0) -> tuple[str, str, Any]:
        if vinculum_units:
            # Extend Gentium's original radical cap, keeping the hook intact.
            # No substituted glyph, drawn line, or Unicode combining overline.
            if char != '√' or self.key != 'GS' or self.name(char) != 'radical':
                raise ValueError('Native vinculum extension requires Gentium 7 Semibold U+221A')
            name = f'radical-vinculum-{vinculum_units:g}'
            if name not in self.paths:
                source = RecordingPen()
                self.glyph_set['radical'].draw(source)
                path_pen, bounds_pen = SVGPathPen(self.glyph_set), BoundsPen(self.glyph_set)
                for operation, args in source.value:
                    new_args = tuple(
                        (x + vinculum_units if x >= 1240 and y >= 1300 else x, y)
                        for x, y in args
                    )
                    getattr(path_pen, operation)(*new_args)
                    getattr(bounds_pen, operation)(*new_args)
                self.paths[name] = (path_pen.getCommands(), bounds_pen.bounds)
            return name, *self.paths[name]
        # A radical is mathematical layout, not a glyph plus a Unicode overline.
        # Ask the font's OpenType MATH table for the native assembled construction.
        if char == '√' and self.key == 'RM':
            name = 'radical.math-assembly'
            if name not in self.paths:
                math = self.tt['MATH'].table.MathVariants
                base_name = self.name(char)
                glyphs = math.VertGlyphCoverage.glyphs
                construction = math.VertGlyphConstruction[glyphs.index(base_name)]
                parts = construction.GlyphAssembly.PartRecords
                if len(parts) < 2:
                    raise ValueError('The configured math font lacks a radical assembly')
                bottom, top = parts[0], parts[-1]
                overlap = min(bottom.EndConnectorLength, top.StartConnectorLength)
                top_y = bottom.FullAdvance - overlap
                path_pen, bounds_pen = SVGPathPen(self.glyph_set), BoundsPen(self.glyph_set)
                for part, offset_y in ((bottom, 0), (top, top_y)):
                    transform = (1, 0, 0, 1, 0, offset_y)
                    self.glyph_set[part.glyph].draw(TransformPen(path_pen, transform))
                    self.glyph_set[part.glyph].draw(TransformPen(bounds_pen, transform))
                self.paths[name] = (path_pen.getCommands(), bounds_pen.bounds)
            return (name, *self.paths[name])
        name = self.name(char)
        if name not in self.paths:
            p, b = SVGPathPen(self.glyph_set), BoundsPen(self.glyph_set)
            self.glyph_set[name].draw(p)
            self.glyph_set[name].draw(b)
            self.paths[name] = (p.getCommands(), b.bounds)
        return (name, *self.paths[name])

    def positions(self, txt: str, size: float, tracking: float) -> list[float]:
        feature = ['ss01'] if self.family == 'Jost*' else None
        return [float(self.metric.getlength(txt[:i], features=feature)) / 1000 * size + i * tracking
                for i in range(len(txt))]



def read_archive_font(archive: zipfile.ZipFile, requested: str) -> bytes:
    """Resolve the exact font face in both supported upstream ZIP layouts.

    The font-only Jost archive uses OpenType/, whereas the official 3.5
    release archive uses fonts/otf/. This must never change the chosen face.
    """
    names = archive.namelist()
    if requested in names:
        resolved = requested
    else:
        name = Path(requested).name
        if requested.startswith('OpenType/'):
            matches = [p for p in names if p == 'fonts/otf/' + name
                       or p.endswith('/fonts/otf/' + name)]
        elif requested.startswith('Gentium-7.000/'):
            matches = [p for p in names if p.endswith('/Gentium-7.000/' + name)]
        else:
            matches = []
        if len(matches) != 1:
            raise ValueError(f'{archive.filename}: expected {requested}, alternatives={matches}')
        resolved = matches[0]
    print(f'{archive.filename}: {requested} -> {resolved}')
    return archive.read(resolved)


class Fonts:
    def __init__(self, data: dict[str, Any], assets: Path, theta_path: Path, math_path: Path, radical_path: Path) -> None:
        with zipfile.ZipFile(assets / 'Jost.zip') as z:
            jb = read_archive_font(z, data['fonts']['JB'])
            jm = read_archive_font(z, data['fonts']['JM'])
            js = read_archive_font(z, data['fonts']['JS'])
        with zipfile.ZipFile(assets / 'Gentium-7.000.zip') as z:
            gs = read_archive_font(z, data['fonts']['GS'])
            gsi = read_archive_font(z, data['fonts']['GSI'])
        self.fonts: dict[str, Font] = {
            'JB': Font('JB', jb, 'Jost*', 400, 'normal'),
            'JM': Font('JM', jm, 'Jost*', 500, 'normal'),
            'JS': Font('JS', js, 'Jost*', 600, 'normal'),
            'GS': Font('GS', gs, 'Gentium', 600, 'normal'),
            'GSI': Font('GSI', gsi, 'Gentium', 600, 'italic'),
            'NSI': Font('NSI', theta_path.read_bytes(), 'Noto Sans', 600, 'italic'),
            'NM': Font('NM', math_path.read_bytes(), 'Noto Sans Math', 400, 'normal'),
            'RM': Font('RM', radical_path.read_bytes(), 'Asana Math', 400, 'normal'),
        }

    def __getitem__(self, key: str) -> Font:
        return self.fonts[key]
