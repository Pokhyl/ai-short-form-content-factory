"""Run with FFmpeg; exercises the real renderer without starting HTTP services."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text()
module = ast.parse(source)
function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == '_render_segment')
namespace = {'subprocess': subprocess, 'VISUAL_MEDIA_TYPES': {'photo', 'video'}}
exec(compile(ast.Module(body=[function], type_ignores=[]), '<renderer>', 'exec'), namespace)
with tempfile.TemporaryDirectory() as tmp:
    for width, height in [(1600, 1611), (1920, 1080), (1080, 1920)]:
        # Edge landmarks must remain visible after fitting; center crop loses them.
        row = b'\xff\x00\x00' * (width // 4) + b'\xff\xff\xff' * (width - 2 * (width // 4)) + b'\x00\x00\xff' * (width // 4)
        fixture = Path(tmp) / 'edges.ppm'
        fixture.write_bytes(f'P6\n{width} {height}\n255\n'.encode() + row * height)
        output = Path(tmp) / 'segment.mp4'
        namespace['_render_segment'](fixture, 'photo', 300, output)
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        assert len(pixels) == 1080 * 1920 * 3
        def pixel(x, y):
            i = (y * 1080 + x) * 3
            return pixels[i:i+3]
        red, blue = pixel(100, 960), pixel(980, 960)
        assert red[0] > 200 and red[1] < 40 and red[2] < 40, (width,height,red)
        assert blue[2] > 200 and blue[0] < 40 and blue[1] < 40, (width,height,blue)
        if width / height > 1080 / 1920:
            assert max(pixel(540, 10)) < 20
        print(json.dumps({'input_size':[width,height],'output_size':[1080,1920],'edge_landmarks_preserved':True}))
