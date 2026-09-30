from __future__ import annotations

import argparse
from pathlib import Path

from hpcalc_svg.loader import load_design
from hpcalc_svg.renderer import build_artifacts


def main() -> None:
    cli = argparse.ArgumentParser(description='Build data-driven SVG/PNG artifacts for HP calculator front views.')
    sub = cli.add_subparsers(dest='command', required=True)

    build = sub.add_parser('build', help='Build SVG and PNG outputs from a design JSON file')
    build.add_argument('--design', type=Path, default=Path('design/hp39gplus.json'))
    build.add_argument('--assets', type=Path, required=True, help='Directory containing Jost.zip and Gentium-7.000.zip')
    build.add_argument('--theta-font', type=Path, default=Path('/usr/share/fonts/truetype/noto/NotoSans-SemiBoldItalic.ttf'))
    build.add_argument('--math-font', type=Path, default=Path('/usr/share/fonts/truetype/noto/NotoSansMath-Regular.ttf'))
    build.add_argument('--radical-font', type=Path, default=Path('/usr/share/fonts/opentype/asana-math/Asana-Math.otf'), help='Asana Math OTF with OpenType MATH radical assembly')
    build.add_argument('--out', type=Path, default=Path('output'))

    args = cli.parse_args()
    if args.command == 'build':
        design = load_design(args.design)
        digest = build_artifacts(design, args.design, args.assets, args.theta_font, args.math_font, args.radical_font, args.out)
        print('design_sha256', digest)
        print('output', args.out)


if __name__ == '__main__':
    main()
