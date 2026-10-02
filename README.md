# hp-calcs-svg

[![CI](https://img.shields.io/github/actions/workflow/status/zyf722/hp-calcs-svg/build.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/zyf722/hp-calcs-svg/actions/workflows/build.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-D22128?logo=apache&logoColor=white)](LICENSE)
![Codex vibe coding](https://img.shields.io/badge/vibe_coded_with-Codex-412991?logo=data:image/svg%2bxml;base64,PHN2ZyB3aWR0aD0iMzg2IiBoZWlnaHQ9IjM4NiIgdmlld0JveD0iMTY1IDE2NSAzODYgMzg2IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJNNTA4Ljc0OSAzMTcuMzk5QzUxNi43NzcgMjg3LjMxNCA1MDguOTkxIDI1My44ODQgNDg1LjM4OSAyMzAuMjgyQzQ2MS43ODggMjA2LjY4MSA0MjguMzYgMTk4Ljg5NSAzOTguMjczIDIwNi45MjNDMzc2LjIzMSAxODQuOTI4IDM0My4zOSAxNzQuOTU2IDMxMS4xNDggMTgzLjU5NkMyNzguOTA2IDE5Mi4yMzQgMjU1LjQ1IDIxNy4yOTIgMjQ3LjM2IDI0Ny4zNjFDMjE3LjI5MSAyNTUuNDUxIDE5Mi4yMzMgMjc4LjkxIDE4My41OTUgMzExLjE0OUMxNzQuOTU3IDM0My4zOTEgMTg0LjkyNyAzNzYuMjMyIDIwNi45MjQgMzk4LjI3NEMxOTguODk2IDQyOC4zNTkgMjA2LjY4MyA0NjEuNzg5IDIzMC4yODQgNDg1LjM5MUMyNTMuODg1IDUwOC45OTIgMjg3LjMxMyA1MTYuNzc5IDMxNy40MDEgNTA4Ljc1QzMzOS40NDIgNTMwLjc0NSAzNzIuMjg2IDU0MC43MTcgNDA0LjUyNSA1MzIuMDc5QzQzNi43NjcgNTIzLjQ0MSA0NjAuMjIzIDQ5OC4zODQgNDY4LjMxMyA0NjguMzE1QzQ5OC4zODMgNDYwLjIyNCA1MjMuNDQgNDM2Ljc2NiA1MzIuMDc4IDQwNC41MjZDNTQwLjcxNiAzNzIuMjg1IDUzMC43NDcgMzM5LjQ0MyA1MDguNzQ5IDMxNy40MDJWMzE3LjM5OVpNNDcwLjg5OSAyNDQuNzc2QzQ4Ni44OTIgMjYwLjc3IDQ5My40ODggMjgyLjYwMSA0OTAuNjg3IDMwMy40MTJMNDE1LjU3NyAyNjAuMDQ2QzQxMi40MTEgMjU4LjIxOCA0MDguNTA5IDI1OC4yMTggNDA1LjM0NSAyNjAuMDQ2TDMxNy40MDEgMzEwLjgyVjI3Ny41MjZDMzE3LjQwMSAyNzUuMTkxIDMxOC42NTIgMjczLjAwNSAzMjAuNjc2IDI3MS44MzdMMzg3LjY0NCAyMzMuMTc0QzQxNC4xNzggMjE4LjM1MyA0NDguMzQ2IDIyMi4yMjMgNDcwLjkwMSAyNDQuNzc2SDQ3MC44OTlaTTM1Ny44MzcgMzExLjE0NEwzOTguMjc1IDMzNC40OTFWMzgxLjE4NUwzNTcuODM3IDQwNC41MzJMMzE3LjM5OCAzODEuMTg1VjMzNC40OTFMMzU3LjgzNyAzMTEuMTQ0Wk0yNjQuNzc2IDI2OS42OTNDMjY1LjIwNyAyMzkuMzA1IDI4NS42NDQgMjExLjY0OSAzMTYuNDUzIDIwMy4zOTNDMzM4LjMgMTk3LjU0IDM2MC41MDUgMjAyLjc0NCAzNzcuMTI3IDIxNS41NzNMMzAyLjAxNCAyNTguOTM3QzI5OC44NDggMjYwLjc2NCAyOTYuODk4IDI2NC4xNDQgMjk2Ljg5OCAyNjcuNzk4VjM2OS4zNDZMMjY4LjA2NSAzNTIuNjk5QzI2Ni4wNDMgMzUxLjUzMSAyNjQuNzc2IDM0OS4zNTMgMjY0Ljc3NiAzNDcuMDE3VjI2OS42OTFWMjY5LjY5M1pNMjAzLjM5MSAzMTYuNDU0QzIwOS4yNDQgMjk0LjYwOCAyMjQuODU0IDI3Ny45NzggMjQ0LjI3NiAyNjkuOTk5VjM1Ni43M0MyNDQuMjc2IDM2MC4zODQgMjQ2LjIyNiAzNjMuNzYzIDI0OS4zOTIgMzY1LjU5MUwzMzcuMzM3IDQxNi4zNjVMMzA4LjUwMyA0MzMuMDEzQzMwNi40ODEgNDM0LjE4MSAzMDMuOTYxIDQzNC4xODggMzAxLjkzOSA0MzMuMDJMMjM0Ljk3MSAzOTQuMzU3QzIwOC44NjggMzc4Ljc4OSAxOTUuMTM4IDM0Ny4yNjEgMjAzLjM5MSAzMTYuNDU0Wk0yNDQuNzc1IDQ3MC45QzIyOC43ODEgNDU0LjkwNiAyMjIuMTg2IDQzMy4wNzUgMjI0Ljk4NiA0MTIuMjY0TDMwMC4wOTYgNDU1LjYzQzMwMy4yNjMgNDU3LjQ1NyAzMDcuMTY0IDQ1Ny40NTcgMzEwLjMyOCA0NTUuNjNMMzk4LjI3MyA0MDQuODU2VjQzOC4xNDlDMzk4LjI3MyA0NDAuNDg1IDM5Ny4wMjIgNDQyLjY3MSAzOTQuOTk3IDQ0My44MzlMMzI4LjAyOSA0ODIuNTAyQzMwMS40OTUgNDk3LjMyMiAyNjcuMzI3IDQ5My40NTIgMjQ0Ljc3MiA0NzAuOUgyNDQuNzc1Wk00NTAuODk3IDQ0NS45ODJDNDUwLjQ2NiA0NzYuMzcxIDQzMC4wMjkgNTA0LjAyNyAzOTkuMjIgNTEyLjI4M0MzNzcuMzczIDUxOC4xMzYgMzU1LjE2OCA1MTIuOTMyIDMzOC41NDcgNTAwLjEwMkw0MTMuNjU5IDQ1Ni43MzhDNDE2LjgyNiA0NTQuOTExIDQxOC43NzUgNDUxLjUzMiA0MTguNzc1IDQ0Ny44NzdWMzQ2LjMyOUw0NDcuNjA5IDM2Mi45NzdDNDQ5LjYzMSAzNjQuMTQ1IDQ1MC44OTcgMzY2LjMyMyA0NTAuODk3IDM2OC42NTlWNDQ1Ljk4NVY0NDUuOTgyWk01MTIuMjgyIDM5OS4yMjFDNTA2LjQyOSA0MjEuMDY4IDQ5MC44MTkgNDM3LjY5NyA0NzEuMzk3IDQ0NS42NzZWMzU4Ljk0NkM0NzEuMzk3IDM1NS4yOTIgNDY5LjQ0OCAzNTEuOTEyIDQ2Ni4yODEgMzUwLjA4NUwzNzguMzM2IDI5OS4zMTFMNDA3LjE3IDI4Mi42NjNDNDA5LjE5MiAyODEuNDk1IDQxMS43MTIgMjgxLjQ4NyA0MTMuNzM0IDI4Mi42NTVMNDgwLjcwMiAzMjEuMzE4QzUwNi44MDUgMzM2Ljg4NyA1MjAuNTM2IDM2OC40MTUgNTEyLjI4MiAzOTkuMjIxWiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg==)

Data-driven SVG recreations of classic HP graphing calculators. Shared chassis geometry, keyboard layouts, typography, and model-specific finishes are described in reusable JSON and rendered into editable/outlined SVGs plus PNG previews.

## Gallery
Built svg and png files are hosted on the [`artifact`](https://github.com/zyf722/hp-calcs-svg/tree/artifact) branch:

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
  <tr>
    <td align="center" colspan="2">
      <a href="https://github.com/zyf722/hp-calcs-svg/blob/artifact/hp50g-blue/HP50gBlue_outlined.svg"><img src="https://media.githubusercontent.com/media/zyf722/hp-calcs-svg/artifact/hp50g-blue/HP50gBlue_preview.png" width="260" alt="HP 50g (blue)"></a><br>
      <strong>HP 50g (blue)</strong>
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
├── hp50g.json
└── hp50g-blue.json
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
