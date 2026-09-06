"""Regenerate the native icon family from the editable SVG. Requires librsvg and macOS iconutil."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / 'macos/Brand/PrecisionCut.svg'
    resources = ROOT / 'macos/Resources'
    resources.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='studio-icons-') as temp:
        iconset = Path(temp) / 'AppIcon.iconset'
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                suffix = '@2x' if scale == 2 else ''
                subprocess.run(['rsvg-convert', '-w', str(size*scale), '-h', str(size*scale), '-o', str(iconset/f'icon_{size}x{size}{suffix}.png'), str(source)], check=True)
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(resources/'AppIcon.icns')], check=True)
    for name, size in [('StudioMark.png', 256), ('AppIcon.png', 1024)]:
        subprocess.run(['rsvg-convert', '-w', str(size), '-h', str(size), '-o', str(resources/name), str(source)], check=True)

if __name__ == '__main__':
    main()
