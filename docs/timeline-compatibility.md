# Timeline compatibility and export validation

`schemas/timeline.schema.json` describes the existing cutaway, overlay, split and insert timeline shapes. `tools.timeline_extensions.apply_timeline_extensions` returns a deep copy and preserves unknown properties and repeated references to the same shot asset. It does not rewrite historical files.

`tools/bake.py` validates this contract before creating output or launching FFmpeg. It rejects invalid shot types, reversed/empty ranges, nonfinite JSON numbers, missing split boxes and invalid render settings. Preview clipping remains supported: a shot may extend beyond the selected preview end. Bake dimensions must be even and FPS an integer; fractional-FPS baking is not implemented and no longer silently truncates the rate.

The optional `extensions` array reserves declarations with `id`, `version`, `target`, `start_frame`, `end_frame`, `parameters` and `time_policy`. Empty or absent extensions preserve legacy behavior. **No declarative effect handler is registered yet.** Every nonempty declaration fails with its unsupported ID/version; it cannot silently disappear from the render. Existing effects authored inside Remotion shots still work. Crossfade, punch-in/spotlight and color-grade handlers remain a later Task 12 deliverable, each requiring explicit timing policy and real render qualification.

## Export preservation

Bake uses a unique temporary directory instead of deleting a shared scratch directory. Final output is encoded to a staged file, its duration is checked against the timeline within one frame or 40 ms (whichever is larger), and only then is the previous export replaced. Failure retains the previous export and scratch evidence. Writing over the input master is rejected. This is failure preservation, not resumable render scheduling or a concurrency coordinator.

## Evidence

Focused regressions reproduce unsupported-extension bypass and a final encoder failure that writes partial bytes. Both now fail safely. The legacy 3.3-second master/cutaway timeline was rendered again: decoded video and audio SHA-256 hashes matched the pre-change output exactly. Receipt: `work/benchmarks/bake-compatibility.json` on the M4 checkout. This is one legacy fixture, not universal compatibility proof or a physical lip-sync measurement.
