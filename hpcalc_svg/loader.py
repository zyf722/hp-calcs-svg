from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from hpcalc_svg.models import JsonObject, validate_raw_design, validate_resolved_design


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = {k: deepcopy(v) for k, v in base.items()}
        for key, value in override.items():
            if key == 'extends':
                continue
            merged[key] = deep_merge(merged[key], value) if key in merged else deepcopy(value)
        return merged
    return deepcopy(override)


def load_design(path: Path, _stack: frozenset[Path] = frozenset()) -> JsonObject:
    """Merge shared defaults and resolve model-to-model vector-geometry references.

    A path may specify ``source_path: './other.json#outer-shell'`` and then
    override only its style or transform. The reference is resolved from JSON,
    not from a compiled SVG, and circular dependencies are rejected.
    """
    path = path.resolve()
    if path in _stack:
        raise ValueError(f'Cyclic design reference: {path}')
    stack = _stack | {path}
    loaded = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(loaded, dict):
        raise TypeError(f'Design root must be an object: {path}')
    raw = cast(JsonObject, loaded)
    validate_raw_design(raw)
    merged: JsonObject = {}
    for rel in raw.get('extends', []):
        merged = deep_merge(merged, load_design(path.parent / rel, stack))
    merged = deep_merge(merged, raw)
    if 'paths' in merged:
        resolved: list[JsonObject] = []
        for part in merged['paths']:
            if 'source_path' not in part:
                resolved.append(part)
                continue
            ref = part['source_path']
            filename, marker, part_id = ref.partition('#')
            if not marker or not filename or not part_id:
                raise ValueError(f'Invalid geometry reference: {ref}')
            referenced = load_design(path.parent / filename, stack)
            matches = [p for p in referenced['paths'] if p['id'] == part_id]
            if len(matches) != 1:
                raise ValueError(f'Expected exactly one path {part_id!r} in {filename!r}')
            resolved.append(deep_merge(matches[0], {k:v for k,v in part.items() if k!='source_path'}))
        merged['paths'] = resolved

    path_remove = merged.pop('path_remove', None)
    if path_remove:
        if not isinstance(path_remove, list) or not all(isinstance(item, str) for item in path_remove):
            raise TypeError('path_remove must be a list of path ids')
        existing = {part.get('id') for part in merged.get('paths', [])}
        missing = set(path_remove) - existing
        if missing:
            raise ValueError(f'Unknown path_remove ids: {sorted(missing)}')
        merged['paths'] = [part for part in merged.get('paths', []) if part.get('id') not in path_remove]

    path_overrides = merged.pop('path_overrides', None)
    if path_overrides:
        if not isinstance(path_overrides, dict):
            raise TypeError('path_overrides must be an object')
        found_paths: set[str] = set()
        paths = merged.get('paths', [])
        for index, part in enumerate(paths):
            part_id = part.get('id')
            if part_id in path_overrides:
                paths[index] = deep_merge(part, path_overrides[part_id])
                found_paths.add(part_id)
        missing_paths = set(path_overrides) - found_paths
        if missing_paths:
            raise ValueError(f'Unknown path_overrides: {sorted(missing_paths)}')
    # Non-path component geometry resolves before descendants inherit this design.
    display = merged.get('display')
    if isinstance(display, dict) and display.get('bezel_ref'):
        ref = display.pop('bezel_ref')
        filename, marker, part_id = ref.partition('#')
        if not filename or not marker or not part_id:
            raise ValueError(f'Invalid bezel_ref: {ref}')
        referenced = load_design(path.parent / filename, stack)
        matches = [p for p in referenced.get('paths', []) if p['id'] == part_id]
        if len(matches) != 1 or not matches[0].get('d'):
            raise ValueError(f'Expected exactly one geometry for {ref}')
        display['bezel'] = matches[0]['d']

    # Derived models may patch a small number of keys without copying the
    # parent's complete rows array. Overrides are merged by stable key id.
    keyboard = merged.get('keyboard')
    if isinstance(keyboard, dict):
        key_overrides = keyboard.pop('key_overrides', None)
        if key_overrides:
            found: set[str] = set()
            for row in keyboard.get('rows', []):
                for index, key in enumerate(row.get('keys', [])):
                    key_id = key.get('id')
                    if key_id in key_overrides:
                        row['keys'][index] = deep_merge(key, key_overrides[key_id])
                        found.add(key_id)
            missing = set(key_overrides) - found
            if missing:
                raise ValueError(f'Unknown keyboard key_overrides: {sorted(missing)}')
    validate_resolved_design(merged)
    return merged
