import pytest

def test_mac_without_nvidia():
    from tools.runtime.encoders import choose_encoder, encoder_args
    assert choose_encoder({'h264_videotoolbox', 'libx264'}, 'auto', 8) == 'h264_videotoolbox'
    args = encoder_args('h264_videotoolbox', 'preview')
    assert args[args.index('-c:v') + 1] == 'h264_videotoolbox'
    assert '-rc' not in args

def test_cpu_and_ten_bit():
    from tools.runtime.encoders import choose_encoder, encoder_args
    assert choose_encoder({'libx264'}, 'auto', 8) == 'libx264'
    assert choose_encoder({'libx265'}, 'auto', 10) == 'libx265'
    args = encoder_args('libx265', 'final')
    assert args[args.index('-pix_fmt') + 1] == 'yuv420p10le'
    with pytest.raises(ValueError):
        choose_encoder({'libx264'}, 'auto', 10)

def test_requested_encoder_is_not_silently_substituted():
    from tools.runtime.encoders import choose_encoder
    with pytest.raises(ValueError):
        choose_encoder({'libx264'}, 'h264_nvenc', 8)

def test_project_path_resolves_unicode(tmp_path):
    from tools.runtime.paths import resolve_project_path
    assert resolve_project_path(tmp_path, 'videos/my ü project') == tmp_path / 'videos/my ü project'
    assert resolve_project_path(tmp_path, str(tmp_path / 'absolute')) == tmp_path / 'absolute'
