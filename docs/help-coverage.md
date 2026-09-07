# Help coverage audit

The authoritative help is `docs/user-guide.json`. This audit maps visible controls, dynamic options and all 18 skills to articles. It is a source audit, not an interactive acceptance or media qualification claim.

| Control, option or capability | Article ID | Evidence source |
|---|---|---|
| New; Create production folder; folder name/location; cancel | `create-production` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift |
| Open; Open production folder; persisted project | `open-production` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift |
| All sidebar tabs; production title/path; busy indicator | `find-your-way` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift |
| Refresh; notices; save semantics; draft loss | `save-and-refresh` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift; all five native views |
| Export handoff; clipboard | `export-handoff` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift |
| Start a first edit | `first-edit` | docs/mac-studio.md; docs/providers.md; config/studio-workflow.json |
| Audience | `brief-audience` | macos/Sources/Studio/IntakeView.swift |
| What should the viewer understand? | `brief-purpose` | macos/Sources/Studio/IntakeView.swift |
| Desired length | `brief-length` | macos/Sources/Studio/IntakeView.swift |
| Tone and pacing | `brief-tone` | macos/Sources/Studio/IntakeView.swift |
| Keep or emphasize | `brief-required` | macos/Sources/Studio/IntakeView.swift |
| Context and editing instructions | `brief-context` | macos/Sources/Studio/IntakeView.swift |
| Save brief; Reload saved brief; dirty/baseline warning | `brief-conflict` | macos/Sources/Studio/IntakeView.swift |
| Import media or documents; file multi-select; drop target; asset list/roles | `import-sources` | macos/Sources/Studio/IntakeView.swift; macos/Sources/Studio/Workspace.swift |
| Solo podcast visuals; Primary audio; Optional camera; No camera; Visual density; Restrained/Balanced/Illustrative; Save/Clear/Reload podcast setup; setup-only and synchronization limits | `podcast-setup` | macos/Sources/Studio/IntakeView.swift; macos/Sources/StudioCore/PodcastConfiguration.swift |
| Label; https://…; Use as; Reference; Source; Background; Add link; saved Link | `add-resource-link` | macos/Sources/Studio/IntakeView.swift |
| Intake stage; prerequisites/artifacts/status | `stage-intake` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Source understanding stage; prerequisites/artifacts/status | `stage-source-understanding` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Editorial strategy stage; prerequisites/artifacts/status | `stage-editorial-strategy` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Edit stage; prerequisites/artifacts/status | `stage-edit` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Final review stage; prerequisites/artifacts/status | `stage-final-review` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Stage picker; What was established, and where is it documented?; Select evidence files; paths; Record evidence | `record-stage-evidence` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Open authoritative workflow | `read-workflow` | macos/Sources/Studio/UnderstandingView.swift; config/studio-workflow.json |
| Viewing; Choose a source or revision; player playback/seek; unresolved count | `review-media` | macos/Sources/Studio/ReviewView.swift |
| Review area; Podcast visual score; current/stale binding; Reload score; episode density timeline and text ranges; chapter picker; proposal details/provenance/camera/transcript; representative preview; Accept proposal; Keep base stage; Reject proposal; revision-bound confirmation | `review-podcast-visual-score` | macos/Sources/Studio/ReviewView.swift; macos/Sources/Studio/PodcastVisualScoreReviewView.swift; macos/Sources/StudioCore/PodcastVisualScore.swift |
| Long-form qualification; Reload qualification; live current/historical status and stale reasons; target/bindings/runtime/memory/pressure/cache/exact A/V streams/decode; required-review statuses; safety record; Attempt history; truthful failure/interruption recovery and preservation | `review-podcast-qualification` | macos/Sources/Studio/PodcastQualificationView.swift; macos/Sources/StudioCore/PodcastQualification.swift; tools/podcast_qualification.py |
| Add revision; Add rendered revision file picker | `add-revision` | macos/Sources/Studio/ReviewView.swift; macos/Sources/Studio/Workspace.swift |
| Pause & capture frame; captured time/notice; Optional range end (seconds); What should change here, and why?; Save annotation | `annotate-frame` | macos/Sources/Studio/ReviewView.swift |
| Audio-only source; Pause & mark time; audio marker notice; frame-free time/range/transcript annotation | `annotate-audio` | macos/Sources/Studio/ReviewView.swift; macos/Sources/StudioCore/PodcastConfiguration.swift |
| Draw region toggle; drag overlay; Clear region | `annotate-region` | macos/Sources/Studio/ReviewView.swift |
| Transcript anchors disclosure; dynamic word/time toggles; no matching transcript | `transcript-anchors` | macos/Sources/Studio/ReviewView.swift |
| Feedback on this version; note time button; status; marked frame; range/transcript labels; History | `inspect-feedback` | macos/Sources/Studio/ReviewView.swift |
| Resolve or reopen; Replacement revision; Choose revision; Resolution notes; Addressed; Ready for review; Accept correction | `resolve-feedback` | macos/Sources/Studio/ReviewView.swift |
| Reopen; transition-disabled states | `reopen-feedback` | macos/Sources/Studio/ReviewView.swift |
| Provider preference dynamic pickers; project route persistence; M4 resource limit | `choose-resources` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| Editorial; codex-astra, codex-sol, local-pair | `route-editorial` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| Transcription; local-qwen | `route-transcription` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| Cleanup; local-deepfilternet | `route-cleanup` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| Images; local-klein, native-codex | `route-images` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| Rendering; local-ffmpeg, local-remotion | `route-rendering` | macos/Sources/Studio/ResourcesView.swift; config/studio-workflow.json; docs/providers.md |
| ChatGPT subscription; account label; Check sign-in; Checking…; Sign in with ChatGPT | `sign-in` | macos/Sources/Studio/CodexView.swift |
| Reopen current sign-in; Cancel sign-in; localhost recovery | `recover-sign-in` | macos/Sources/Studio/CodexView.swift |
| Codex model; GPT-6 Astra; GPT-5.6 Sol | `choose-codex-model` | macos/Sources/Studio/CodexView.swift; docs/benchmarks/first-release.md |
| Production task prompt; Send to Codex; Working…; task ID; messages/error | `send-task` | macos/Sources/Studio/CodexView.swift |
| Stop task | `stop-task` | macos/Sources/Studio/CodexView.swift; docs/known-limits.md |
| Codex needs your response; dynamic question fields; Send answers; Approve this action; Decline | `answer-codex` | macos/Sources/Studio/CodexView.swift |
| Final production QA; Before; During; After; passed; pending / findings | `qa-findings` | macos/Sources/Studio/CodexView.swift; docs/production-quality-workflow.md |
| Open authoritative rules | `production-rules` | macos/Sources/Studio/CodexView.swift |
| Local application paths; Engine repository; Python executable; Codex executable; Save paths | `local-paths` | macos/Sources/Studio/CodexView.swift |
| How to Use tab/menu; Section; All sections; Search help; Clear search; result count; No matching help | `use-help` | macos/Sources/Studio/HelpView.swift; macos/Sources/Studio/StudioApp.swift |
| Help for this tab; context sheet; Done | `context-help` | macos/Sources/Studio/HelpView.swift; macos/Sources/Studio/StudioApp.swift |
| Copy example | `copy-help-example` | macos/Sources/Studio/HelpView.swift; macos/Sources/Studio/StudioApp.swift |
| Reload help; source label; fallback reason; missing-guide state | `reload-help` | macos/Sources/Studio/HelpView.swift; macos/Sources/Studio/StudioApp.swift |
| $edit-video | `skill-edit-video` | .agents/skills/edit-video/SKILL.md |
| $clean-cut | `skill-clean-cut` | .agents/skills/clean-cut/SKILL.md |
| $clean-audio | `skill-clean-audio` | .agents/skills/clean-audio/SKILL.md |
| $brand-setup | `skill-brand-setup` | .agents/skills/brand-setup/SKILL.md |
| $make-tsx; overlay/cutaway/split/insert; split box/crop center/zoom | `skill-make-tsx` | .agents/skills/make-tsx/SKILL.md; tools/bake.py; schemas/timeline.schema.json |
| $vidtsx-2d-generator | `skill-vidtsx-2d-generator` | .agents/skills/vidtsx-2d-generator/SKILL.md |
| $fake-screencast | `skill-fake-screencast` | .agents/skills/fake-screencast/SKILL.md |
| $generate-image | `skill-generate-image` | .agents/skills/generate-image/SKILL.md |
| $thumbnail | `skill-thumbnail` | .agents/skills/thumbnail/SKILL.md |
| $packaging | `skill-packaging` | .agents/skills/packaging/SKILL.md |
| $suggest-sfx | `skill-suggest-sfx` | .agents/skills/suggest-sfx/SKILL.md |
| $music | `skill-music` | .agents/skills/music/SKILL.md |
| $voiceover | `skill-voiceover` | .agents/skills/voiceover/SKILL.md |
| $shorts | `skill-shorts` | .agents/skills/shorts/SKILL.md |
| $avatar | `skill-avatar` | .agents/skills/avatar/SKILL.md |
| $generate-video | `skill-generate-video` | .agents/skills/generate-video/SKILL.md |
| $tracker | `skill-tracker` | .agents/skills/tracker/SKILL.md |
| $publish-video | `skill-publish-video` | .agents/skills/publish-video/SKILL.md |
| legacy Mode Edited/Raw; tight/natural; segment; play this; cut this; restore; edge drag; start/end ±50ms; Save; Render preview; jump to it; timeline legend | `legacy-cut-editor` | tools/editor/index.html; .agents/skills/clean-cut/SKILL.md |
| legacy Space; E; arrows; Shift arrows; comma/period; I/O/C; +/-; zoom slider | `legacy-editor-shortcuts` | tools/editor/index.html |
| crossfade in/out; punch-in zoom/center; color-grade brightness/contrast/saturation; timeline vs Remotion controls | `timeline-effects` | docs/timeline-compatibility.md |
| Historical feedback only; integrity warning; disabled capture | `missing-media` | macos/Sources/Studio/ReviewView.swift |
| Action needs attention; OK; disabled controls | `disabled-action` | macos/Sources/Studio/StudioApp.swift; macos/Sources/Studio/Workspace.swift; all five native views |
| Open Diagnostic Logs | `diagnostic-logs` | macos/Sources/Studio/StudioApp.swift; macos/Sources/StudioCore/Diagnostics.swift |
| provider readiness; no fallback; memory limits | `provider-not-ready` | docs/providers.md; docs/known-limits.md |
| native image dispatch/import recovery | `interrupted-image` | docs/providers.md; docs/known-limits.md |
| planned research; raw-footage qualification; scheduler/editor limits | `unfinished-capabilities` | docs/mac-studio.md; docs/known-limits.md; plan/Editorial Techniques — Implementation Roadmap.md; plan/Short-Form Vertical Video Research and Studio Specification.html |

## Qualification and maintenance

- Native instructions were checked against all five original views, StudioApp and Workspace. Help controls were also checked against the implemented HelpView: Search help, Clear search, Section/All sections, result count, Copy example, Reload help, source/fallback messages and empty/error states.
- All 18 `.agents/skills/*/SKILL.md` files were read. Historical hosted commands and fixed delivery assumptions are subordinate to current provider, memory and production policies; the guide does not instruct their execution.
- Provider and production claims were checked against docs/providers.md, docs/known-limits.md, docs/implementation-status.md, docs/benchmarks/first-release.md and docs/mac-studio.md.
- Separate browser editor controls were checked in tools/editor/index.html. Its comma/period shortcut uses a hard-coded 59.94 rate; the guide calls out this limitation.
- Review acceptance uses the exact transition graph in ReviewView.canTransition. Every transition requires notes; non-open destinations require a replacement revision.
- Draft preservation is limited: contextual help leaves the view underneath, but ordinary tab/project navigation is not a general autosave contract.
- No production, hosted generation, model download, publication test or upload was run for this documentation task.
- Planned editorial/short-form research is explicitly labeled; authentic raw-footage and full audiovisual qualification remain production-specific work.

Content inventory: 78 articles across 9 sections; 18 primary skill articles.
