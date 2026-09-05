# Timeline compatibility and effects

`schemas/timeline.schema.json` describes existing cutaway, overlay, split and insert timelines. `tools.timeline_extensions.apply_timeline_extensions` validates and returns a deep copy, preserving unknown properties and repeated shot asset references. `bake.py` validates before creating output or launching FFmpeg. Malformed ranges, nonfinite values, unsupported versions/parameters and invalid render settings fail clearly.

## Version 1 extensions

All effects require `time_policy: "preserve"`. They change pixels without consuming handles, overlapping timeline duration or moving audio. Ranges use integer frames, start-inclusive/end-exclusive, at `preview.fps`. List order determines the order of output effects.

| ID | Target and clock | Parameters |
|---|---|---|
| `crossfade` | One uniquely named cutaway; start/end must equal that shot's master-clock bounds | `in_frames`, `out_frames` (integers, nonnegative, positive sum no longer than the shot) |
| `punch-in` | `output`; frames on the final clock including inserts | `zoom` 1–4 (default 1.5), `center_x`/`center_y` 0–1 (default .5) |
| `color-grade` | `output`; frames on the final clock including inserts | `brightness` −1–1 (default 0), `contrast` 0–2 (default 1), `saturation` 0–3 (default 1) |

A cutaway crossfade blends the moving master and moving shot during its existing slot, then returns to the master. It uses a linear blend in the encoded color space, not scene-linear colorimetry. The master audio continues unchanged. It cannot overlap another visual shot; compose complex layers inside Remotion instead. Inserts retain their existing pause/resume semantics.

```json
{
  "id": "crossfade", "version": 1, "target": "OpeningCard",
  "start_frame": 30, "end_frame": 120,
  "parameters": {"in_frames": 12, "out_frames": 12},
  "time_policy": "preserve"
}
```

This example requires a unique `OpeningCard` cutaway from master seconds 1 to 4 at 30 FPS. Grade/punch-in output effects run in a staged postprocess, re-encoding video and copying audio. Do not promise bit-identical picture outside the effect after a lossy re-encode. Empty/absent extensions retain the old rendering path.

## Remotion authoring

Reusable `Crossfade`, `PunchIn` and `ColorGrade` components live in `remotion/src/lib/extensions/`. Pass `version={1}` and explicit frame ranges. They preserve the composition clock. `ExtensionProof` demonstrates all three in a 90-frame composition.

Remotion `ColorGrade` uses CSS multipliers (neutral brightness 1), while the FFmpeg timeline grade uses additive brightness (neutral 0). These are separate authoring controls; do not copy brightness values between them assuming equivalence.

## Validation and preservation

Preview clipping remains supported. Bake dimensions must be even; FPS must be an integer. Fractional-FPS baking is not implemented and is rejected rather than silently truncated. Tiny split boxes fail before encoding.

Bake uses a unique scratch directory, encodes to staged files and checks final duration within one frame or 40 ms (whichever is larger) before replacing the previous export. Failure retains the prior export and scratch evidence. Overwriting the input master is rejected. This is failure preservation, not a concurrency coordinator or resumable scheduling engine.

## Evidence

Real FFmpeg pixel tests check red→blue→red cutaway blending, bounded crop location and bounded grade brightness while retaining exactly 60 frames. Unsupported/shadowed declarations fail. The legacy 3.3-second timeline retained identical decoded video/audio hashes without extensions. `ExtensionProof` rendered 90 frames with external network access denied; representative crossfade, punch and grade frames were inspected. Receipts/artifacts are in `work/benchmarks/`. These are functional fixtures, not physical lip-sync or broad creative-quality certification.
