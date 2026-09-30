# hp-calcs-svg

[![CI](https://img.shields.io/github/actions/workflow/status/zyf722/hp-calcs-svg/build.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/zyf722/hp-calcs-svg/actions/workflows/build.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-D22128?logo=apache&logoColor=white)](LICENSE)
![Codex](https://img.shields.io/badge/vibe_coded_with-Codex-412991)

Data-driven SVG recreations of classic HP graphing calculators. Shared chassis geometry, keyboard layouts, typography, and model-specific finishes are described in reusable JSON and rendered into editable/outlined SVGs plus PNG previews.

## Gallery

<div align="center">
<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp39gplus/HP39gplus_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp39gplus/HP39gplus_preview.png" width="260" alt="HP 39g+"></a><br>
      <strong>HP 39g+</strong>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp39gs/HP39gs_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp39gs/HP39gs_preview.png" width="260" alt="HP 39gs"></a><br>
      <strong>HP 39gs</strong>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp40gs/HP40gs_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp40gs/HP40gs_preview.png" width="260" alt="HP 40gs"></a><br>
      <strong>HP 40gs</strong>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp48gii/HP48gII_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp48gii/HP48gII_preview.png" width="260" alt="HP 48gII"></a><br>
      <strong>HP 48gII</strong>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp49gplus/HP49gplus_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp49gplus/HP49gplus_preview.png" width="260" alt="HP 49g+"></a><br>
      <strong>HP 49g+</strong>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp50g/HP50g_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp50g/HP50g_preview.png" width="260" alt="HP 50g"></a><br>
      <strong>HP 50g</strong>
    </td>
  </tr>
</table>
</div>

## Build

Requires Python 3.11–3.13, Poetry 2, Inkscape, Jost 3.5, Gentium 7.000, Noto Sans / Noto Sans Math, and Asana Math.

```bash
poetry install
poetry run hpcalc-svg build \
  --design design/hp50g.json \
  --assets /path/to/font-archives \
  --out output50
```

CI builds all models and publishes `*_editable.svg`, `*_outlined.svg`, `*_preview.png`, and `resolved_design.json` to the `artifact` branch. PNG previews use Git LFS.

## Design

```text
design/
├── common/
│   ├── base.json       # shared rendering defaults
│   └── chassis.json    # shared physical curves
├── hp39gplus.json
├── hp39gs.json
├── hp40gs.json
├── hp48gii.json
├── hp49gplus.json
└── hp50g.json
```

Derived models use `extends` plus targeted `path_overrides`, `path_remove`, and keyboard `key_overrides` instead of copying parent geometry. Pydantic validates source descriptors and resolved designs before rendering.

## Lint

```bash
poetry run ruff check hpcalc_svg
poetry run mypy hpcalc_svg
```

## License

Original project code, JSON design data, and vector work are licensed under [Apache-2.0](LICENSE).

This is an independent, unofficial project and is not affiliated with or endorsed by HP Inc. HP trademarks remain the property of their respective owner. The badge geometry comes from Wikimedia Commons' [HP logo 2008.svg](https://commons.wikimedia.org/wiki/File:HP_logo_2008.svg); see [NOTICE](NOTICE) for third-party and trademark details.
