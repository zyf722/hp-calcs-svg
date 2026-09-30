from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

from hpcalc_svg.fonts import Component, Fonts

NS = 'http://www.w3.org/2000/svg'
XML = 'http://www.w3.org/XML/1998/namespace'
ET.register_namespace('', NS)


def svg_tag(tag: str) -> str:
    return f'{{{NS}}}{tag}'


def attrs(obj: Mapping[str, object]) -> dict[str, str]:
    return {k.replace('_', '-'): str(v) for k, v in obj.items()}


class Renderer:
    def __init__(self, design: dict[str, Any], fonts: Fonts, project_root: Path, outlined: bool = True, digest: str = '') -> None:
        self.d: dict[str, Any] = design
        self.f: Fonts = fonts
        self.outlined: bool = outlined
        self.project_root: Path = project_root
        width, height = design['metadata']['canvas']
        self.root = ET.Element(svg_tag('svg'), {
            'viewBox': f'0 0 {width} {height}', 'width': str(width), 'height': str(height),
            'role': 'img', 'aria-label': f"{design['metadata']['name']} faithful flat front view",
            'data-source-sha256': digest,
        })
        ET.SubElement(self.root, svg_tag('title')).text = f"{design['metadata']['name']} front-view vector redraw"
        ET.SubElement(self.root, svg_tag('desc')).text = 'Generated only from JSON design layers. Blank LCD. Jost*, Gentium, Noto Sans and Asana Math glyph sources.'
        self.defs = ET.SubElement(self.root, svg_tag('defs'))
        self.bounds: dict[str, tuple[float, float, float, float]] = {}
        artwork = design['metadata'].get('artwork_viewbox')
        if artwork:
            self.scene = ET.SubElement(self.root, svg_tag('g'), {
                'id': 'artwork',
                'transform': f'scale({width / artwork[0]:.9f} {height / artwork[1]:.9f})',
            })
        else:
            self.scene = self.root

    def geometry_transform(self, component: Mapping[str, Any]) -> str | None:
        """Resolve shared 665x1340 geometry in model-specific photo space."""
        if component.get('coordinate_space') == 'base':
            artwork = self.d['metadata'].get('artwork_viewbox')
            if not artwork:
                return None
            width, height = self.d['metadata']['canvas']
            return f'scale({artwork[0] / width:.12f} {artwork[1] / height:.12f})'
        return cast(str | None, component.get('transform'))

    def group(self, p: ET.Element, name: str, **extra: object) -> ET.Element:
        return ET.SubElement(p, svg_tag('g'), attrs({'id': name, **extra}))

    def path(self, p: ET.Element, d: str, **extra: object) -> ET.Element:
        return ET.SubElement(p, svg_tag('path'), attrs({'d': d, **extra}))

    def rect(self, p: ET.Element, x: float, y: float, w: float, h: float, r: float = 0, **extra: object) -> ET.Element:
        return ET.SubElement(p, svg_tag('rect'), attrs({'x': x, 'y': y, 'width': w, 'height': h, 'rx': r, **extra}))

    def circle(self, p: ET.Element, x: float, y: float, r: float, **extra: object) -> ET.Element:
        return ET.SubElement(p, svg_tag('circle'), attrs({'cx': x, 'cy': y, 'r': r, **extra}))

    def gradients(self) -> None:
        for name, cols in self.d['gradients'].items():
            grad = ET.SubElement(self.defs, svg_tag('linearGradient'), {'id': name, 'x1': '0', 'y1': '0', 'x2': '0', 'y2': '1'})
            for i, color in enumerate(cols):
                ET.SubElement(grad, svg_tag('stop'), {'offset': str(i / (len(cols) - 1)), 'stop-color': color})
        for fid, std in [('blur2', 2), ('blur4', 4), ('blur6', 6)]:
            fil = ET.SubElement(self.defs, svg_tag('filter'), {'id': fid, 'x': '-25%', 'y': '-25%', 'width': '150%', 'height': '150%'})
            ET.SubElement(fil, svg_tag('feGaussianBlur'), {'stdDeviation': str(std)})

    def text(self, p: ET.Element, name: str, components: list[Component], color: str, mode: str, x: float, y: float, role: str) -> tuple[float, float, float, float]:
        group = self.group(p, name, data_role=role, data_label=''.join(c.text for c in components))
        glyphs: list[tuple[str, str, str, float, float, float]] = []
        box = [math.inf, math.inf, -math.inf, -math.inf]
        for c in components:
            font = self.f[c.font]
            for char, advance in zip(c.text, font.positions(c.text, c.size, c.tracking), strict=True):
                glyph, path, b = font.glyph(char, c.vinculum_units if char == '√' else 0)
                if not path or b is None:
                    continue
                sc = c.size / font.upm
                ix0, ix1 = c.dx + advance + b[0] * sc, c.dx + advance + b[2] * sc
                iy0, iy1 = c.dy - b[3] * sc, c.dy - b[1] * sc
                box = [min(box[0], ix0), min(box[1], iy0), max(box[2], ix1), max(box[3], iy1)]
                glyphs.append((c.font, glyph, path, c.dx + advance, c.dy, sc))
        if not glyphs:
            raise ValueError('Empty text label: ' + name)
        if mode == 'center':
            delta_x, delta_y = x - (box[0] + box[2]) / 2, y - (box[1] + box[3]) / 2
        elif mode == 'left':
            delta_x, delta_y = x - box[0], y - (box[1] + box[3]) / 2
        elif mode == 'right':
            delta_x, delta_y = x - box[2], y - (box[1] + box[3]) / 2
        elif mode == 'top-left':
            delta_x, delta_y = x - box[0], y - box[1]
        else:
            raise ValueError('Unknown label alignment: ' + mode)
        bounds = (box[0] + delta_x, box[1] + delta_y, box[2] + delta_x, box[3] + delta_y)
        self.bounds[name] = bounds
        group.set('data-bbox', ','.join(f'{value:.3f}' for value in bounds))
        group.set('fill', color)
        # Keep assembled MATH glyphs as font-derived vector outlines even in the
        # editable SVG. An editable Unicode √ would discard its actual top bar.
        if self.outlined or any('√' in c.text and (c.font == 'RM' or c.vinculum_units) for c in components):
            for font_key, glyph, path, gx, gy, sc in glyphs:
                self.path(group, path,
                          transform=f'translate({delta_x + gx:.5f},{delta_y + gy:.5f}) scale({sc:.9f},-{sc:.9f})',
                          data_font=font_key, data_glyph=glyph)
        else:
            for c in components:
                f = self.f[c.font]
                feature = "font-feature-settings:'ss01' 1;" if f.family == 'Jost*' else ''
                node = ET.SubElement(group, svg_tag('text'), {
                    'x': f'{delta_x + c.dx:.5f}', 'y': f'{delta_y + c.dy:.5f}',
                    'font-family': f.family, 'font-weight': str(f.weight), 'font-style': f.style,
                    'font-size': str(c.size), 'letter-spacing': str(c.tracking),
                    'style': f"font-family:'{f.family}';font-weight:{f.weight};font-style:{f.style};letter-spacing:{c.tracking}px;{feature}",
                    f'{{{XML}}}space': 'preserve',
                })
                node.text = c.text
        return bounds

    def parts(self, raw: str | list[dict[str, Any]], font: str = 'JB', size: float = 16) -> list[Component]:
        if isinstance(raw, str):
            return [Component(raw, font=font, size=size)]
        return [Component(text=p['text'], font=p.get('font', font), size=p.get('size', size),
                          dx=p.get('dx', 0), dy=p.get('dy', 0), tracking=p.get('tracking', -0.14), vinculum_units=p.get('vinculum_units', 0)) for p in raw]

    def shell(self) -> None:
        g = self.group(self.scene, 'housing')
        for item in self.d['paths']:
            styling = {k: v for k, v in item.items() if k not in ('d', 'coordinate_space')}
            transform = self.geometry_transform(item)
            if transform:
                styling['transform'] = transform
            self.path(g, item['d'], **styling)

    def screen(self) -> None:
        s = self.d['display']
        g = self.group(self.scene, 'display')
        self.path(g, s['bezel'], fill=s.get('bezel_fill', self.d['palette']['bezel']), stroke=s['bezel_stroke'], stroke_width=s['bezel_stroke_width'], **({'transform': s['bezel_transform']} if s.get('bezel_transform') else {}))
        if s.get('screen_path'):
            self.path(g, s['screen_path'], fill=s.get('screen_fill', self.d['palette']['glass']),
                      stroke=s['screen_stroke'], stroke_width=s['screen_stroke_width'])
        else:
            self.rect(g, *s['screen'], fill=s.get('screen_fill', self.d['palette']['glass']),
                      stroke=s['screen_stroke'], stroke_width=s['screen_stroke_width'])

    def logo(self) -> None:
        d = self.d['logo']
        g = self.group(self.scene, 'hp-logo', data_source=d['source_page'])
        self.rect(g, *d['rect'], fill=d['badge_fill'], stroke=d['badge_stroke'], stroke_width=d['badge_stroke_width'])

        asset = self.project_root / d['asset']
        if not asset.is_file():
            raise FileNotFoundError(f'Missing HP logo asset: {asset}')
        source = ET.parse(asset).getroot()
        source_group = next((node for node in source if node.tag.endswith('g')), None)
        source_path = next((node for node in source.iter() if node.tag.endswith('path')), None)
        if source_group is None or source_path is None or not source_path.get('d'):
            raise ValueError(f'Unexpected Wikimedia HP logo structure: {asset}')

        x, y, w, h = d['svg']
        mark = ET.SubElement(g, svg_tag('svg'), {
            'x': str(x),
            'y': str(y),
            'width': str(w),
            'height': str(h),
            'viewBox': '0 0 1000 999.98',
            'overflow': 'visible',
            'preserveAspectRatio': 'xMidYMid meet',
        })
        source_transform = source_group.get('transform')
        if source_transform:
            target = ET.SubElement(mark, svg_tag('g'), {'transform': source_transform})
        else:
            target = mark
        self.path(target, source_path.get('d') or '', fill=d['fill'])

    def header(self) -> None:
        d = self.d['header']
        g = self.group(self.scene, 'header-print')
        x, sz = d['x'], d['font_size']
        brand_bounds = self.text(g, 'hp', self.parts(d['brand_text'], d.get('brand_font', 'JS'), sz), d['text_color'], 'top-left', x, d['top_y'], 'header')
        label = d['subtitle']
        font = self.f['JB']
        index = label.index('p')
        prefix = font.metric.getlength(label[:index], features=['ss01']) / 1000 * sz
        _, _, b = font.glyph('p')
        if d.get('brand_model_gap') is not None:
            p_left = brand_bounds[2] + d['brand_model_gap']
        else:
            p_left = d.get('model_x', x + prefix + b[0] * sz / font.upm)
        self.text(g, 'model', self.parts([{'text': d['model_text'], 'tracking': d.get('model_tracking', -0.14)}], 'JB', sz),
                  d['text_color'], 'top-left', p_left, d['top_y'], 'header')
        subtitle_tracking = d.get('subtitle_tracking', -0.14)
        self.text(g, 'description', self.parts([{'text': label, 'tracking': subtitle_tracking}], 'JB', sz),
                  d['text_color'], 'top-left', x, d['second_y'], 'header')
        if not d.get('show_triangle', True):
            return
        if d.get('triangle_after_last_char_positions') is not None:
            positions = font.positions(label, sz, subtitle_tracking)
            visible_ink: list[tuple[float, float] | None] = []
            for ch, pos in zip(label, positions, strict=True):
                _, _, bounds = font.glyph(ch)
                visible_ink.append(None if bounds is None else
                                   (pos + bounds[0] * sz / font.upm,
                                    pos + bounds[2] * sz / font.upm))
            ink_left = min(item[0] for item in visible_ink if item is not None)
            last_index = max(i for i, item in enumerate(visible_ink) if item is not None)
            target = visible_ink[last_index]
            if target is None:
                raise ValueError('IrDA target must be a visible glyph')
            last_char = label[last_index]
            advance = (font.metric.getlength(last_char, features=['ss01']) / 1000 * sz
                       + subtitle_tracking)
            tri_x = (x + (target[0] + target[1]) / 2 - ink_left
                     + d['triangle_after_last_char_positions'] * advance
                     + d.get('triangle_x_offset', 0))
        else:
            second_l = label.lower().index('calculator') + d.get('triangle_char_index', 5)
            adv = font.metric.getlength(label[:second_l], features=['ss01']) / 1000 * sz
            # The mark was positioned against the default -0.14 tracking.
            # Preserve that optical calibration while following the actual label.
            adv += second_l * (subtitle_tracking - (-0.14))
            wid = font.metric.getlength(label[second_l], features=['ss01']) / 1000 * sz
            tri_x = d.get('triangle_x', x + adv + wid / 2) + d.get('triangle_x_offset', 0)
            if d.get('triangle_ink_anchor'):
                # Anchor to the actual visible ink of the target subtitle glyph,
                # correcting for Jost ss01, tracking, and top-left ink alignment.
                # Keep the approved 39g+ anchor untouched via model opt-in.
                glyph_ink: list[tuple[float, float] | None] = []
                for ch, pos in zip(label, font.positions(label, sz, subtitle_tracking), strict=True):
                    _, _, bounds = font.glyph(ch)
                    glyph_ink.append(None if bounds is None else
                                     (pos + bounds[0] * sz / font.upm,
                                      pos + bounds[2] * sz / font.upm))
                ink_left = min(item[0] for item in glyph_ink if item is not None)
                target = glyph_ink[second_l]
                if target is None:
                    raise ValueError('IrDA target must be a visible glyph')
                tri_x = x + (target[0] + target[1]) / 2 - ink_left + d.get('triangle_x_offset', 0)
        top, bottom = d['triangle_y']
        half = d['triangle_half_width']
        self.path(g, f'M{tri_x:.3f} {top:.3f} L{tri_x - half:.3f} {bottom:.3f} H{tri_x + half:.3f} Z',
                  fill=d['triangle_color'], data_anchor=d.get('triangle_anchor_name', 'calculator-second-l'))

    def fn_keys(self) -> None:
        d = self.d['function_keys']
        g = self.group(self.scene, 'six-function-keys', **({'transform': self.geometry_transform(d)} if self.geometry_transform(d) else {}))
        for i, cx in enumerate(d['centers'], 1):
            k = self.group(g, f'F{i}')
            self.rect(k, cx - d['width'] / 2, d['y'], d['width'], d['height'], d['radius'], fill=d['fill'], stroke=d['stroke'], stroke_width=d['stroke_width'])
            if d.get('items'):
                item = d['items'][i - 1]
                if item.get('top'):
                    self.text(k, f'fn{i}-top', self.parts(item['top'], 'JM', d.get('top_size', 14)), d.get('top_color', '#194861'), 'center', cx, d['y'] - d.get('top_offset', 14), 'fn-top')
                main = self.parts(item['label'], 'JS', d.get('label_size', 19))
                letter = self.parts(item['letter'], 'JS', d.get('letter_size', 15)) if item.get('letter') else None
                main_x = cx - 6
                letter_x = cx + d['width'] * .28
                if letter and d.get('composite_center', False):
                    main_w, letter_w = self.ink_width(main), self.ink_width(letter)
                    gap = d.get('composite_gap', 4)
                    if main_w + letter_w + gap > d['width'] - 2 * d.get('composite_side_margin', 4):
                        raise ValueError(f'F{i} label+letter exceed key face')
                    main_x, letter_x = self.composite_centers(cx, main_w, letter_w, gap)
                self.text(k, f'fn{i}-label', main, d.get('label_color', '#f6f6f7'), 'center', main_x, d['y'] + d['height']/2, 'fn')
                if letter:
                    self.text(k, f'fn{i}-letter', letter, d.get('letter_color', '#efcc5c'), 'center', letter_x + d.get('letter_offset_x', 0), d['y'] + d['height']/2 + d.get('letter_offset_y', 0), 'fn-alpha')

    def navigation(self) -> None:
        d = self.d['nav']
        g = self.group(self.scene, 'navigation', **({'transform': self.geometry_transform(d)} if self.geometry_transform(d) else {}))
        if d.get('recess_path'):
            r = self.group(g, 'recess')
            soft = d['soft_well']
            # Entire depression uses only softened fills/shadows. No hard perimeter stroke.
            self.path(r, d['recess_path'], fill=soft['shadow_fill'], opacity=soft['shadow_opacity'],
                      filter=f"url(#{soft['shadow_blur']})", transform=f"translate(0 {soft['shadow_offset_y']})")
            self.path(r, d['recess_path'], fill=soft['ambient_shadow_fill'], opacity=soft['ambient_shadow_opacity'],
                      filter='url(#blur6)', transform='translate(0.8 1.2)')
            self.path(r, d['recess_path'], fill=soft['body_fill'], opacity=soft['body_opacity'],
                      filter=f"url(#{soft['body_blur']})")
            self.path(r, d['recess_path'], fill=soft['ambient_highlight_fill'], opacity=soft['ambient_highlight_opacity'],
                      filter='url(#blur6)', transform='translate(-0.9 -1.1)')
            self.path(r, d['recess_path'], fill='none', stroke=soft['highlight_color'],
                      stroke_width=soft['highlight_width'], opacity=soft['highlight_opacity'],
                      filter=f"url(#{soft['highlight_blur']})", transform=f"translate({soft['highlight_dx']} {soft['highlight_dy']})")
            self.path(r, d['recess_path'], fill='none', stroke=soft['depth_color'],
                      stroke_width=soft['depth_width'], opacity=soft['depth_opacity'],
                      filter=f"url(#{soft['depth_blur']})", transform=f"translate({soft['depth_dx']} {soft['depth_dy']})")
        for item in d['buttons']:
            name, cx, cy, angle = item['id'], item['cx'], item['cy'], item['rotation']
            b = self.group(g, name)
            ox, oy = d['shadow_offset']
            self.circle(b, cx + ox, cy + oy, d['outer_radius'] + d['shadow_radius_extra'], fill=d['shadow_fill'], opacity=d['soft_well']['button_shadow_opacity'], filter=f"url(#{d['soft_well']['button_shadow_blur']})")
            self.circle(b, cx, cy, d['outer_radius'], fill=d['outer_fill'], stroke=d['outline'], stroke_width=d['outline_width'])
            w, up, dn = d['arrow_half_width'], d['arrow_up'], d['arrow_down']
            self.path(b, f'M{cx} {cy - up} L{cx - w} {cy + dn} L{cx + w} {cy + dn} Z',
                      fill=d['glyph_fill'], stroke=d['glyph_stroke'], stroke_width=d['glyph_stroke_width'], transform=f'rotate({angle} {cx} {cy})')

    @staticmethod
    def key_path(cx: float, cy: float, w: float, h: float, r: float, bulge: float, lip_inset: float, lip_profile: str = 'quadratic') -> str:
        x, y = cx - w / 2, cy - h / 2
        bottom = y + h - lip_inset
        if lip_profile == 'side_to_side_cubic':
            # The entire lower edge is ONE cubic joining the vertical side
            # endpoints, with vertical tangents at both ends. No additional
            # bottom-corner transitions, split lobes or center seam.
            # Its midpoint lies 3/4 of the control-point drop below side_y,
            # preserving the former bottom + bulge at the center.
            side_y = bottom - r
            control_y = side_y + (r + bulge) * 4 / 3
            return (f'M{x+r:.3f} {y:.3f} H{x+w-r:.3f} '
                    f'Q{x+w:.3f} {y:.3f} {x+w:.3f} {y+r:.3f} '
                    f'V{side_y:.3f} C{x+w:.3f} {control_y:.3f} '
                    f'{x:.3f} {control_y:.3f} {x:.3f} {side_y:.3f} '
                    f'V{y+r:.3f} Q{x:.3f} {y:.3f} {x+r:.3f} {y:.3f} Z')
        if lip_profile != 'quadratic':
            raise ValueError(f'Unknown key lip profile: {lip_profile}')
        # Preserve the original quadratic geometry for the 49g+ profile.
        return (f'M{x+r:.3f} {y:.3f} H{x+w-r:.3f} '
                f'Q{x+w:.3f} {y:.3f} {x+w:.3f} {y+r:.3f} '
                f'V{bottom-r:.3f} Q{x+w:.3f} {bottom:.3f} {x+w-r:.3f} {bottom:.3f} '
                f'Q{cx:.3f} {bottom+bulge:.3f} {x+r:.3f} {bottom:.3f} '
                f'Q{x:.3f} {bottom:.3f} {x:.3f} {bottom-r:.3f} '
                f'V{y+r:.3f} Q{x:.3f} {y:.3f} {x+r:.3f} {y:.3f} Z')

    @staticmethod
    def composite_centers(cx: float, main_width: float, letter_width: float, gap: float) -> tuple[float, float]:
        """Center a two-color legend as one optical group using ink widths."""
        if min(main_width, letter_width) <= 0 or gap < 0:
            raise ValueError('Invalid composite-legend dimensions')
        return cx - (letter_width + gap) / 2, cx + (main_width + gap) / 2

    def ink_width(self, components: list[Component]) -> float:
        """Measure actual visible glyph ink for a centered two-color key."""
        left, right = math.inf, -math.inf
        for comp in components:
            font = self.f[comp.font]
            for char, advance in zip(comp.text, font.positions(comp.text, comp.size, comp.tracking), strict=True):
                _, path, bounds = font.glyph(char, comp.vinculum_units if char == '√' else 0)
                if not path or bounds is None:
                    continue
                scale = comp.size / font.upm
                left = min(left, comp.dx + advance + bounds[0]*scale)
                right = max(right, comp.dx + advance + bounds[2]*scale)
        return right-left if left < right else 0

    def keys(self) -> dict[str, tuple[ET.Element, dict[str, Any], dict[str, Any]]]:
        d = self.d['keyboard']
        g = self.group(self.scene, 'keyboard')
        table: dict[str, tuple[ET.Element, dict[str, Any], dict[str, Any]]] = {}
        for row in d['rows']:
            rid, cy, default_size, h = row['id'], row['center_y'], row['default_size'], row['height']
            grid = d.get('grids', {}).get(row.get('grid'))
            if row.get('grid') and (grid is None or len(grid) != len(row['keys'])):
                raise ValueError(f'Invalid keyboard grid for {rid}')
            for column, obj in enumerate(row['keys']):
                cx = grid[column] if grid is not None else obj['cx']
                kid, w, kind, label = obj['id'], obj['width'], obj['kind'], obj['label']
                k = self.group(g, 'key-' + kid, data_kind=kind, data_center=f'{cx},{cy}')
                fill = d['kind_fill'][kind]
                stroke = d.get('kind_stroke', {}).get(kind, self.d['palette']['navy_border'])
                self.path(k, self.key_path(cx, cy, w, h, d['radius'], d['bottom_bulge'], d['lower_lip_inset'], d.get('lip_profile', 'quadratic')), fill=fill, stroke=stroke, stroke_width=d['outline_width'])
                table[kid] = (k, row, obj)
                color = self.d['palette'][d['kind_text'][kind]]
                if kid == 'dot':
                    self.circle(k, cx, cy, d['dot_radius'], fill=color)
                special = obj.get('main_parts')
                if obj.get('glyph_path'):
                    self.path(k, obj['glyph_path'], fill=color, data_role='main-symbol')
                elif kid != 'dot' and (label or special):
                    parts = self.parts(special if special is not None else label, 'JS', obj.get('main_size', default_size))
                    fixed_primary = rid in d.get('inline_primary_rows', ())
                    main_y = cy + (d.get('inline_primary_center_dy', 0) if fixed_primary else d['ink_offset_y']) - (6.0 if obj.get('key_alpha_position') == 'below' else 0.0)
                    pair = obj.get('key_alpha') and obj.get('key_alpha_position') != 'below' and d.get('inline_alpha', False)
                    if pair:
                        alpha_parts = self.parts(obj['key_alpha'], 'JM', obj.get('key_alpha_size', obj.get('main_size', default_size)))
                        main_w, alpha_w = self.ink_width(parts), self.ink_width(alpha_parts)
                        spacing = d.get('inline_alpha_min_gap', d.get('inline_alpha_gap', 3.0))
                        if d.get('inline_alpha_layout') == 'fixed_right':
                            # Reserve the right-hand ALPHA lane, then center the
                            # primary printing in the remaining left-hand region.
                            alpha_x = cx + d['inline_alpha_fixed_dx']
                            edge = d.get('inline_alpha_edge_margin', 1.0)
                            if alpha_x + alpha_w / 2 > cx + w / 2 - edge + .01:
                                raise ValueError(f'ALPHA letter exceeds key cap: {kid}')
                            main_x = (cx if fixed_primary and kid in d.get('inline_primary_full_center_ids', ())
                                      else cx + d.get('inline_primary_center_dx', 0)
                                      if fixed_primary else cx + obj.get('main_dx', 0))
                            if main_x + main_w / 2 + spacing > alpha_x - alpha_w / 2 + .01:
                                raise ValueError(f'Main+ALPHA ink collision: {kid}')
                            if main_x - main_w / 2 < cx - w / 2 + edge - .01:
                                raise ValueError(f'Main+ALPHA cannot fit key: {kid}')
                        else:
                            if main_w + spacing + alpha_w > w - d.get('inline_alpha_side_margin', 5):
                                raise ValueError(f'Composite main+alpha legend too wide for {kid}: {main_w + spacing + alpha_w:.2f}/{w}')
                            main_x = cx - (alpha_w + spacing)/2
                            alpha_x = cx + (main_w + spacing)/2
                        k.set('data-alpha-center', f'{alpha_x:.5f}')
                    else:
                        main_x = cx + obj.get('main_dx', 0)
                    k.set('data-main-center', f'{main_x:.5f}')
                    k.set('data-main-y', f'{main_y:.5f}')
                    self.text(k, 'main-' + kid, parts, color, 'center', main_x, main_y, 'main')
                for glyph in obj.get('glyph_paths', []):
                    styling = {name: value for name, value in glyph.items() if name != 'd'}
                    self.path(k, glyph['d'], **styling, data_role='main-symbol')
                for decoration in obj.get('decorations', []):
                    styling = {name: value for name, value in decoration.items() if name != 'path'}
                    self.path(k, decoration['path'], fill=decoration.get('fill', color), **{name:value for name,value in styling.items() if name!='fill'}, data_role='key-decoration')
                legend_defaults = d.get('legend_defaults', {})
                legend_items = obj.get('legends', [])
                pair_text_size = None
                if len(legend_items) >= 2:
                    candidates: list[float] = []
                    compatible = True
                    for candidate in legend_items[:2]:
                        candidate_font = candidate.get('font', 'JM')
                        if ('path' in candidate or candidate.get('parts') or candidate.get('vector_prefix')
                                or self.f[candidate_font].family != 'Jost*'):
                            compatible = False
                            break
                        candidate_default = (legend_defaults.get('long_size', 10.8)
                                             if len(candidate['text']) >= legend_defaults.get('length_threshold', 6)
                                             else legend_defaults.get('short_size', 12.0))
                        candidate_size = candidate.get('size', candidate_default)
                        max_width = legend_defaults.get(candidate.get('style', 'blue') + '_max_width', float('inf'))
                        width = self.f[candidate_font].metric.getlength(
                            candidate['text'], features=['ss01']) / 1000 * candidate_size
                        if width > max_width:
                            candidate_size = max(legend_defaults.get('min_size', 10.8),
                                                 candidate_size * max_width / width)
                        candidates.append(candidate_size)
                    if compatible:
                        pair_text_size = min(candidates)
                for j, legend in enumerate(legend_items):
                    alignment = legend.get('align', 'center')
                    if alignment == 'left':
                        lx = cx - w / 2 + legend_defaults.get('left_inset', -3) - legend.get('extra_left',0)
                        if len(legend['text']) >= legend_defaults.get('wide_label_threshold', 7):
                            lx -= legend_defaults.get('wide_label_left_shift', 0)
                    elif alignment == 'right':
                        lx = cx + w / 2 - legend_defaults.get('right_inset', -3) + legend.get('extra_right',0)
                    else:
                        lx = cx
                    ly = cy - h / 2 - legend.get('offset', legend_defaults.get('vertical_offset', 11))
                    style = legend.get('style', 'blue')
                    l_color = self.d['palette'][d['legend_colors'][style]]
                    legend_size = (legend_defaults.get('long_size', 10.8) if len(legend['text']) >= legend_defaults.get('length_threshold', 6)
                                   else legend_defaults.get('short_size', 12.0))
                    font_key = legend.get('font', 'JM')
                    size = pair_text_size if pair_text_size is not None and j < 2 else legend.get('size', legend_size)
                    if pair_text_size is None and 'path' not in legend and not legend.get('parts'):
                        # Keep the two-color legends readable without overlap.
                        max_width = legend_defaults.get(style + '_max_width', float('inf'))
                        width = self.f[font_key].metric.getlength(legend['text'], features=['ss01'] if self.f[font_key].family == 'Jost*' else None) / 1000 * size
                        if width > max_width:
                            size = max(legend_defaults.get('min_size', 10.8), size * max_width / width)
                    if 'path' in legend:
                        if legend.get('path_fill'):
                            self.path(g, legend['path'], fill=l_color, stroke='none', data_role=style)
                        else:
                            self.path(g, legend['path'], fill='none', stroke=l_color, stroke_width=legend.get('stroke_width',1.7),
                                      stroke_linecap=legend.get('stroke_linecap','round'),
                                      stroke_linejoin=legend.get('stroke_linejoin','round'), data_role=style)
                    else:
                        if legend.get('vector_prefix'):
                            symbol = self.group(g, f'legend-{kid}-{j}-vector', data_role=style)
                            vector = legend['vector_prefix']
                            if vector.get('stroke'):
                                self.path(symbol, vector['d'], fill='none', stroke=l_color,
                                          stroke_width=vector.get('stroke_width', 1.8),
                                          stroke_linecap=vector.get('stroke_linecap','round'),
                                          stroke_linejoin=vector.get('stroke_linejoin','round'), data_role=style)
                            else:
                                self.path(symbol, vector['d'], fill=l_color, data_role=style)
                        self.text(g, f'legend-{kid}-{j}', self.parts(legend.get('parts', legend['text']), font_key, size),
                                  l_color, alignment, lx, ly, style)
                if obj.get('below_label'):
                    self.text(g, f'below-{kid}', self.parts(obj['below_label'], obj.get('below_font','JB'), obj.get('below_label_size',15)),
                              obj.get('below_color', self.d['palette']['cancel_text']), 'center', cx,
                              cy+h/2+obj.get('below_offset',12), 'below-label')
                if obj.get('key_alpha'):
                    below = obj.get('key_alpha_position') == 'below'
                    alpha_center = k.get('data-alpha-center')
                    alpha_x = cx if below else (float(alpha_center) if alpha_center is not None else cx + w * .36)
                    self.text(k, f'key-alpha-{kid}', self.parts(obj['key_alpha'], 'JM', obj.get('key_alpha_size', obj.get('main_size', default_size))),
                              self.d['palette'][d['legend_colors']['yellow']], 'center', alpha_x,
                              cy+14 if below else (cy + d.get('inline_primary_center_dy', 0) + obj.get('key_alpha_dy', 0) if rid in d.get('inline_primary_rows', ()) else cy+d['ink_offset_y'] + obj.get('key_alpha_dy', 0)), 'key-alpha')
        return table

    def shift(self) -> None:
        if self.d['keyboard'].get('legend_mode') == 'per_key':
            return
        d = self.d['modifiers']
        g = self.group(self.scene, 'shift-legends')
        setup = d['setup']
        color = self.d['palette']['shift']
        ordinary_dx = d.get('normal_shift_dx', 0)
        self.path(g, setup['bracket'], fill='none', stroke=color, stroke_width=1.25)
        setup_x, setup_y = setup['target']
        self.text(g, 'shift-setup', self.parts('SETUP', d['shift_font'], setup['size']), color, 'center', setup_x, setup_y, 'shift')
        for row in self.d['keyboard']['rows']:
            rid = row['id']
            for key in row['keys']:
                label = key.get('shift')
                if not label:
                    continue
                kid, cx, w = key['id'], key['cx'], key['width']
                if label == '∠':
                    angle = d['angle']
                    x, y = angle['vertex']
                    radius = angle['sector_radius']
                    ga = self.group(g, 'shift-angle', fill='none', stroke=color, stroke_width=1.4, stroke_linejoin='round', stroke_linecap='round', transform=f'translate({ordinary_dx} 0)')
                    self.path(ga, f"M{x} {y} H{x + angle['arm_h']} M{x} {y} L{x + 7} {y + angle['arm_y']}", fill='none')
                    self.path(ga, f'M{x + radius * .98} {y - 0.48} A{radius} {radius} 0 0 0 {x + radius * .64} {y - radius * .44}', fill='none')
                    continue
                parts = self.parts(key.get('shift_parts', label), d['shift_font'], d['shift_size'])
                mode = 'center' if rid == 'fnB' else 'left'
                target_x = cx if rid == 'fnB' else cx - w / 2 + 2 + ordinary_dx
                self.text(g, 'shift-' + kid, parts, color, mode, target_x, d['shift_band'][rid], 'shift')

    def alpha(self) -> None:
        if self.d['keyboard'].get('legend_mode') == 'per_key':
            return
        d = self.d['modifiers']
        g = self.group(self.scene, 'alpha-legends')
        color = self.d['palette']['alpha']
        for row in self.d['keyboard']['rows']:
            rid = row['id']
            for key in row['keys']:
                label = key.get('alpha')
                if not label:
                    continue
                kid, cx, w = key['id'], key['cx'], key['width']
                x = (cx + w / 2)
                style = key.get('alpha_style', {})
                font = style.get('font', d['alpha_font'])
                size = style.get('size', d['space_size'] if label == 'SPACE' else d['alpha_size'])
                self.text(g, 'alpha-' + kid, self.parts(label, font, size), color, 'center', x, d['alpha_band'][rid], 'alpha')
        cancel = d['cancel']
        cancel_x, cancel_y = cancel['target']
        self.text(g, 'cancel', self.parts('CANCEL', 'JB', cancel['size']), self.d['palette']['cancel_text'], 'center', cancel_x, cancel_y, 'alpha')

    def validate(self) -> bool:
        ids = [e.get('id') for e in self.root.iter() if e.get('id')]
        assert len(ids) == len(set(ids)), 'duplicate element ids'
        main = [e for e in self.root.iter() if e.get('data-role') == 'main']
        assert len(main) == self.d['metadata'].get('main_key_count', 40), 'unexpected number of main key legends'
        parents = {child: p for p in self.root.iter() for child in p}
        for grp in main:
            bbox = grp.get('data-bbox')
            if bbox is None:
                raise ValueError('main legend is missing data-bbox')
            bb = [float(value) for value in bbox.split(',')]
            center = parents[grp].get('data-center')
            if center is None:
                raise ValueError('key is missing data-center')
            cx, cy = (float(value) for value in center.split(','))
            expected_x = float(parents[grp].get('data-main-center', cx))
            assert abs((bb[0] + bb[2]) / 2 - expected_x) < .01, grp.get('id')
            target_id = (grp.get('id') or '').removeprefix('main-')
            key = next(k for row in self.d['keyboard']['rows'] for k in row['keys'] if k['id'] == target_id)
            main_y = float(parents[grp].get('data-main-y', cy + self.d['keyboard']['ink_offset_y'] - (6.0 if key.get('key_alpha_position') == 'below' else 0.0)))
            assert abs((bb[1] + bb[3]) / 2 - main_y) < .01, grp.get('id')
        if self.d['function_keys'].get('composite_center'):
            gap = self.d['function_keys'].get('composite_gap', 4)
            for i, cx in enumerate(self.d['function_keys']['centers'], 1):
                main_box = self.bounds[f'fn{i}-label']
                letter_box = self.bounds[f'fn{i}-letter']
                letter_dx = self.d['function_keys'].get('letter_offset_x', 0)
                # An intentional letter-only offset advances the pair's outer
                # midpoint by half that offset and increases its ink clearance.
                assert abs((main_box[0] + letter_box[2]) / 2 - (cx + letter_dx / 2)) < .01, f'F{i} pair off-center'
                assert letter_box[0] - main_box[2] >= gap + letter_dx - .01, f'F{i} pair ink collision'
        return True

    def build(self) -> ET.Element:
        self.gradients()
        self.shell()
        self.screen()
        self.logo()
        self.header()
        self.fn_keys()
        self.navigation()
        self.keys()
        self.shift()
        self.alpha()
        self.validate()
        return self.root

    def write(self, file: Path) -> None:
        ET.indent(self.root, space='  ')
        ET.ElementTree(self.root).write(file, encoding='utf-8', xml_declaration=True)


def build_artifacts(design: dict[str, Any], design_path: Path, assets: Path, theta_font: Path, math_font: Path, radical_font: Path, out: Path) -> str:
    original = design_path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    fonts = Fonts(design, assets, theta_font, math_font, radical_font)
    out.mkdir(parents=True, exist_ok=True)
    prefix = design['metadata']['output_prefix']
    for mode, filename in [(True, f'{prefix}_outlined.svg'), (False, f'{prefix}_editable.svg')]:
        renderer = Renderer(design, fonts, design_path.parent.parent, mode, digest)
        renderer.build()
        renderer.write(out / filename)
    # Save resolved design for future variants/migrations.
    (out / 'resolved_design.json').write_text(json.dumps(design, ensure_ascii=False, indent=2), encoding='utf-8')
    # Raster previews are 1.5x the unchanged SVG page dimensions (144/96 DPI).
    subprocess.run(['inkscape', str(out / f'{prefix}_outlined.svg'), '--export-area-page',
                    '--export-type=png', '--export-dpi=144',
                    '--export-background-opacity=0',
                    '--export-filename=' + str(out / f'{prefix}_preview.png')], check=True)
    from PIL import Image
    with Image.open(out / f'{prefix}_preview.png') as png:
        source_width, source_height = design['metadata']['canvas']
        if (abs(png.width - source_width * 1.5) > .5 or
                abs(png.height - source_height * 1.5) > .5):
            raise ValueError(f'Unexpected 1.5x PNG size: {png.size}')
    return digest
