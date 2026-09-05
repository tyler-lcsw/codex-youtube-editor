"""Sample-accurate catalog cue placement."""
def cue_sample(at_ms: int, onset_ms: int, sample_rate: int) -> int:
    if sample_rate<=0 or onset_ms<0 or at_ms<onset_ms:raise ValueError('Cue precedes asset onset or sample rate is invalid')
    return round((at_ms-onset_ms)*sample_rate/1000)
