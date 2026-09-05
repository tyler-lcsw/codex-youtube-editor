import pytest

def test_pause_markup_and_unsupported_controls():
    from tools.voice_script import parse_voice_script
    assert parse_voice_script('Hello.<break time="300ms"/>Again.')==[{'text':'Hello.'},{'silence_ms':300},{'text':'Again.'}]
    with pytest.raises(ValueError):parse_voice_script('<prosody volume="x-loud">Hi</prosody>')
    with pytest.raises(ValueError):parse_voice_script('<break time="-1s"/>')
