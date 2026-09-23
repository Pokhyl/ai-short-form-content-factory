"""Run with FFmpeg; exercises the real still-image renderer without HTTP services."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text()
module = ast.parse(source)
function = next(
    n for n in module.body
    if isinstance(n, ast.FunctionDef) and n.name == '_render_segment'
)
namespace = {'subprocess': subprocess, 'VISUAL_MEDIA_TYPES': {'photo', 'video'}}
exec(
    compile(ast.Module(body=[function], type_ignores=[]), '<renderer>', 'exec'),
    namespace,
)

with tempfile.TemporaryDirectory() as tmp:
    for width, height in [(1600, 1611), (1920, 1080), (1080, 1920)]:
        quarter = width // 4
        row = (
            b'\xff\x00\x00' * quarter
            + b'\xff\xff\xff' * (width - 2 * quarter)
            + b'\x00\x00\xff' * quarter
        )
        fixture = Path(tmp) / f'cover-{width}x{height}.ppm'
        fixture.write_bytes(
            f'P6\n{width} {height}\n255\n'.encode() + row * height
        )
        output = Path(tmp) / f'segment-{width}x{height}.mp4'

        namespace['_render_segment'](fixture, 'photo', 300, output)

        pixels = subprocess.check_output([
            'ffmpeg', '-v', 'error', '-i', str(output),
            '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-',
        ])
        assert len(pixels) == 1080 * 1920 * 3

        def pixel(x, y):
            i = (y * 1080 + x) * 3
            return pixels[i:i + 3]

        # Preserve the complete proportional foreground: the synthetic
        # left/right edge landmarks must remain visible at the frame center.
        red = pixel(100, 960)
        blue = pixel(980, 960)
        assert red[0] > 180 and red[1] < 70 and red[2] < 70, (
            width, height, red
        )
        assert blue[2] > 180 and blue[0] < 70 and blue[1] < 70, (
            width, height, blue
        )

        # The blurred cover background must fill the complete 9:16 canvas,
        # so the old black top/bottom letterbox cannot return.
        fill_probes = [
            pixel(100, 10), pixel(540, 10), pixel(980, 10),
            pixel(100, 1910), pixel(540, 1910), pixel(980, 1910),
        ]
        assert all(max(p) > 80 for p in fill_probes), (
            width, height, fill_probes
        )

        print(json.dumps({
            'input_size': [width, height],
            'output_size': [1080, 1920],
            'edge_landmarks_preserved': True,
            'full_frame_no_black_bars': True,
        }))
