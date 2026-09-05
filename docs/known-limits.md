# Known limits and deferred work

The first release targets one 24 GiB M4 and retains Remotion. The supplied upstream video is not a completion benchmark. These limits remain explicit after autonomous development:

- LM Studio ignores the requested 4K context cap. Short requests are bounded and parallelism verified; long contexts, simultaneous large inference jobs and a universal memory guarantee are unqualified. PAIR routing does not pool memory, and multi-node behavior was not tested.
- Local generated images are limited to 393216 pixels and one reference. Large multi-reference workflows, video/avatar inference and generative music/SFX are deferred. Procedural effects are not substitutes for arbitrary generated audio.
- Voice and image trials are synthetic functional checks. Personal likeness, expressive delivery, difficult-noise equivalence and long-form creative quality require real project review.
- Render ASR has unknown confidence and may flag timing variance. Duration/frame equality does not prove lip sync. The synthetic edit retains one 60 ms ASR timing review flag.
- Bake currently requires integer FPS; fractional-FPS cutting is separately tested. Crossfades target one unique cutaway without overlapping visuals. New effect versions and time-changing transitions require implementation and timing tests.
- Native image dispatch cannot atomically coordinate a local file write with a remote Codex tool call. The one-time marker prevents blind retries, but an interrupted call may require artifact recovery or a new scoped user decision. No live hosted generation was tested.
- The general job cache remains an extension utility, not a complete scheduler for every legacy CLI. Failed bake/cleanup/import work preserves prior artifacts, but universal resume, concurrent-project scheduling and unattended creative approval are not claimed.
- Publication functionality is retained; publication tests and uploads were explicitly waived. Automatic PR merging does not authorize YouTube publication.

Production footage, owner brand choices and personal voice/face references are supplied just in time for an actual video. None is needed to recreate or expand the synthetic setup proof.
