import wave
import pytest

def test_sound_onset_and_procedural_output(tmp_path):
    from tools.audio_assets import cue_sample
    from tools.providers.sfx_procedural import synthesize
    assert cue_sample(2500,120,48000)==114240
    with pytest.raises(ValueError):cue_sample(20,120,48000)
    p=tmp_path/'click.wav';synthesize('click',p,.1,42)
    with wave.open(str(p)) as f:
        assert f.getframerate()==48000 and f.getnframes()==4800
    with pytest.raises(ValueError):synthesize('elephant trumpet',p,.1,42)
