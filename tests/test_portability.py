import subprocess
from pathlib import Path

def test_upload_relative_paths_use_this_repository():
    import tools.yt_upload as upload
    assert upload.rp('videos/example/master.mp4') == Path(__file__).resolve().parents[1] / 'videos/example/master.mp4'

def test_segment_runs_without_cuda(tmp_path):
    from tools.fixture_media import make_clock_clip
    from tools.render_cuts import render_segment
    src = make_clock_clip(tmp_path / 'clock.mp4', '30', 1)
    out = tmp_path / 'part.mp4'
    render_segment(src, (0, .5), out, ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'])
    assert out.stat().st_size > 1000
