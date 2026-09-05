# Benchmark protocol

Visual target: https://www.youtube.com/watch?v=AfBRRsGSKe4. Tyler identifies the entire
visible production as made with the existing workflow. Exact per-asset production provenance
has not been independently established. Use original/cleared content to recreate the techniques.

| Reference window | Case to compare | Mapping status |
|---|---|---|
| 4:39–6:17 | Generated UI/simulated screencast, cursor and animated explanatory assets | Candidate fake-screencast / make-tsx; exact shot mapping pending |
| 6:20–8:07 | Voice cleanup, word-aligned sound cues | clean-audio / suggest-sfx; before/after isolated audio unavailable |
| 8:42–9:29 | Packaging and thumbnails | packaging / thumbnail; image-provider replacement requires separate quality trial |
| 10:52–11:04 | Transitions/effects/filters mentioned as roadmap | Do not label all roadmap effects as shipped |

Initial clock fixture has 640×360 frame numbers, rational FPS, 48 kHz 50 ms audio pulses
at integer seconds and matching visual flashes. Raw PCM positions are authoritative;
AAC delivery priming requires measured QA rather than equating container durations.
Human corpus target: 10–15 minutes, 200 annotated word boundaries, fillers, multiple takes,
noise, accents and proper nouns. Finished reference video does not replace raw ground truth.
Quality thresholds: median word error <=40 ms, p95 <=100 ms; zero accepted harmful cuts;
SFX onset <=1 output frame; landmark A/V drift <=40 ms with no duration-dependent allowance.
Record hardware, revisions, native resolution, runtime, peak memory, swap and rejected assets.
