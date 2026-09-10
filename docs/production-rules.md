# Authoritative video production rules

These rules default to editing supplied footage. Read this file before production, during editing, and at final QA. Edit rules here; the coordinator reads this file at runtime. Stable IDs must not be reused for a different rule. Add new rules with new IDs. All rules require a reasoned disposition at each phase; a plan is not evidence of completion.

Each rule owns the responsibility named in bold. Cross-references identify related checks, not substitutes for them. One evidence artifact may support several rules, but each disposition must explain its distinct finding.

Retired IDs remain reserved: R16 was consolidated into R15; R30 moved to the [workflow qualification contract](workflow-qualification.md). Qualification of a reusable workflow is separate from acceptance of each production. Neither retired ID belongs in new production checklists; historical records retain their original IDs.

The following final QA requirements cannot be waived. This editable metadata is enforced by the coordinator; the rule wording below remains authoritative.

<!-- final-required: R24 R25 R26 R31 -->

## R01

DO **define the editing brief** before cutting: audience, purpose, desired length, pacing, required content, visual style, and delivery formats.

## R02

DO **establish the source's role**: determine whether a supplied YouTube link is the footage to edit or a creative reference. Use the highest-quality available source for the actual edit.

## R03

DO **understand the source** before deciding what to remove. Review its argument, demonstrations, emotional beats, and intended conclusion.

## R04

DO **preserve originals and edit history**: retain original footage, audio, and transcripts. Keep editorial changes reversible and maintain identifiable versions of successful outputs, including through corrective work.

## R05

DO **inspect source properties** before processing: resolution, frame rate, variable-frame-rate behavior, audio channels, sample rate, and existing synchronization. This establishes the input baseline, not final synchronization acceptance under R14.

## R06

DO **build a representative preview** before committing to the full edit. Include difficult speech, a cut, an overlay, and any synchronization-sensitive material relevant to the planned edit; do not add techniques solely to satisfy the preview. Full final playback remains R25.

## R07

DO **preserve the speaker's meaning and verbal identity** when selecting or tightening words. Retain qualifications and characteristic phrasing, rhetorical questions, self-corrections, or comic repetition when they carry meaning or personality. Remove redundancy without changing substance or creating misleading associations between statements. Delivery timing is reviewed under R08.

## R08

DO **preserve meaningful delivery timing**: do not remove every hesitation, breath, or pause automatically. Retain space and reaction timing that support comprehension, emphasis, humor, emotion, or an on-screen action. Word selection is reviewed under R07.

## R09

DO **verify transcript content** against the recording, especially names, numbers, terminology, negations, and apparent mistakes. Automated transcription is assistance, not unquestionable evidence; word-timing integrity is R10.

## R10

DO **maintain trustworthy word timings**: do not invent missing timings or clear alignment warnings merely to make validation pass. Re-align or review the affected passage; preserve uncertainty when it remains unresolved.

## R11

DO **obtain authorization for synthetic replacement speech** and an appropriate reference before regenerating a speaker's words. Do not use regeneration as an unapproved solution to an editing or transcription problem.

## R12

DO **verify cleanup fidelity against the original audio**. Retain cleanup only when it improves intelligibility without introducing distortion, unnatural texture, or damaged speech. Finished-mix intelligibility is R23.

## R13

DO **maintain rendered-timeline mapping** for edits, captions, graphics, and sound cues. Recalculate downstream timing whenever cuts, pauses, speed changes, or inserts change it. Correct mapping does not replace the perceptual synchronization check in R14.

## R14

DO **verify perceptual synchronization** using the recording itself. Check visible speech and relevant on-screen actions; equal durations and matching transcripts alone do not prove synchronization.

## R15

DO **select techniques by editorial purpose**: clarification, evidence, orientation, emphasis, emotional or comic timing, or coherent identity and atmosphere. Every cutaway, zoom, transition, caption, sound cue, and decorative treatment must serve the brief; it need not explain a literal claim. Consider leaving the beat unchanged. Do not force available capabilities into a video, impose fixed cut/caption/effects quotas, or infer effectiveness from a reference video's popularity. A capability demonstration and an audience-facing edit have different success criteria. Apply R17 to factual implications and R19 to readability.

## R17

DO **verify the factual meaning of visuals**. Diagrams, screenshots, images, labels, cursor movements, and highlights presented as evidence or explanation must support the associated claim. Decorative visuals permitted by R15 need not illustrate a claim, but must not imply unsupported facts. Authentic-versus-illustrative presentation is R18; source context and interpretation are R34.

## R18

DO **distinguish illustrative material from authentic recordings** where confusion is possible. Do not present simulated screens or generated imagery as recordings of real events, results, or performance.

## R19

DO **verify visual readability and continuity** at the intended viewing size and actual on-screen duration. Check typography, contrast, color consistency, subject identity, composition, crop boundaries, and text size. Enlarge or isolate dense source passages and charts. Keep host insets, captions, decorative frames, and platform UI from covering essential material. Preserve source context under R34. Attention priority is R32; approved brand identity is R33.

## R20

DO **respect provider qualification and operating limits**: use proven providers within tested memory budgets, dimensions, reference limits, and concurrency constraints. Do not silently substitute an unqualified capability.

## R21

DO **inspect intermediate and provider outputs before incorporation**. Validate each returned artifact, reject incomplete responses, and inspect generated media before using it. A successful request, installed model, or completed process is not proof of usable output. Delivery-file validation, full final playback, and review-status reporting remain separate under R24–R26.

## R22

DO **document asset provenance and permissions**. Keep prompts, references, model versions, and licensing information with the project; use appropriately permitted assets and obtain scoped approval for hosted generation.

## R23

DO **verify finished-mix intelligibility** throughout the video. Review music and effects beneath speech, inspect transitions, and measure final loudness and true peak. Cleanup fidelity against the original is a separate check under R12.

## R24

DO **technically validate the actual delivery files**. Decode them, check dimensions and frame counts, verify audio duration, and confirm that captions and stems align—including inserted silence. These checks do not replace perceptual synchronization or full final playback.

## R25

DO **review the complete final video at normal playback speed with audio**. Representative frames and automated checks supplement this review; they do not replace it.

## R26

DO **report review status honestly**. Do not declare unavailable review steps complete. Distinguish technical validation, visual inspection, listening review, and user acceptance, with unresolved findings clearly identified.

## R27

DO **adapt each delivery format deliberately**. Reassess framing, attention, platform UI, and caption placement while preserving essential context, faces, demonstrations, and readable captions. Do not rely on an automatic center crop or transfer long-form layouts unchanged to Shorts or TikTok.

## R28

DO **keep the packaging promise accurate**: titles, thumbnails, and descriptions must represent the finished edit. Do not promise an outcome or demonstration the video does not deliver. Visual brand consistency is R33.

## R29

DO **correct failures and revalidate affected outputs**. Fix the underlying cause, invalidate stale caches and affected reviews, and add regression coverage for reusable pipeline defects. Preserve originals and successful versions under R04.

## R31

DO **keep publication approval separate from QA**. Publication requires approval of the actual deliverable and destination; do not publish automatically when editing is complete.

## R32

DO **direct attention to the current beat's priority**. Choose host-led commentary, source-dominant inspection, or shared source/reaction layouts where useful; a host inset should add visible reaction or continuity. Change emphasis at meaningful narrative, evidence, or reaction boundaries. Technique selection and non-use are governed by R15, readability by R19, and format adaptation by R27.

## R33

DO **apply the approved project identity** coherently across the video and packaging where applicable. Reuse appropriate typography, color roles, framing, and host/source treatments while allowing story-specific content to vary. Extract principles from references; do not impose another creator's signature template as the project's house style. Use R15 to decide when branding treatments add value and R19 to verify their readability.

## R34

DO **preserve source context and distinguish interpretation**. Separate what a displayed source states from the presenter's inference, opinion, or joke. Retain attribution, dates, qualifications, and surrounding context when needed to understand the claim. Cropping, highlighting, or juxtaposition must not imply stronger evidence or an endorsement than the source provides. Displaying a source is not independent verification of its claims.
