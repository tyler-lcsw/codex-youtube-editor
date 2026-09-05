# Authoritative video production rules

These rules default to editing supplied footage. Read this file before production, during editing, and at final QA. Edit rules here; the coordinator reads this file at runtime. Stable IDs must not be reused for a different rule. Add new rules with new IDs. All rules require a reasoned disposition at each phase; a plan is not evidence of completion.

The following final QA requirements cannot be waived. This editable metadata is enforced by the coordinator; the rule wording below remains authoritative.

<!-- final-required: R24 R25 R26 R31 -->

## R01

DO define the editing brief before cutting: audience, purpose, desired length, pacing, required content, visual style, and delivery formats.

## R02

DO establish whether a supplied YouTube link is the footage to edit or a creative reference. Use the highest-quality available source for the actual edit.

## R03

DO review the source video before deciding what to remove. Understand its argument, demonstrations, emotional beats, and intended conclusion.

## R04

DO preserve original footage, audio, and transcripts. Keep editorial changes reversible and maintain identifiable versions of successful outputs.

## R05

DO inspect source properties before processing: resolution, frame rate, variable-frame-rate behavior, audio channels, sample rate, and existing synchronization.

## R06

DO build a representative preview before committing to the full edit. Include difficult speech, a cut, an overlay, and any synchronization-sensitive material.

## R07

DO preserve the speaker’s meaning, qualifications, and personality. Tighten repetition without changing the substance or creating misleading associations between statements.

## R08

DO NOT remove every hesitation, breath, or pause automatically. Preserve timing that supports comprehension, emphasis, humor, emotion, or an on-screen action.

## R09

DO treat automated transcripts as editing assistance, not unquestionable evidence. Verify names, numbers, terminology, negations, and apparent mistakes against the recording.

## R10

DO NOT invent missing word timings or clear alignment warnings merely to make validation pass. Re-align or review the affected passage; preserve uncertainty when it remains unresolved.

## R11

DO NOT regenerate a speaker’s words to solve an editing or transcription problem. Synthetic replacement speech requires explicit authorization and an appropriate reference.

## R12

DO compare processed audio with the original. Retain cleanup only when it improves intelligibility without introducing distortion, unnatural texture, or damaged speech.

## R13

DO anchor edits, captions, graphics, and sound cues to the actual rendered timeline. Recalculate downstream timing whenever cuts, pauses, speed changes, or inserts change it.

## R14

DO verify synchronization using the recording itself. Check visible speech and relevant on-screen actions; equal durations and matching transcripts alone do not prove synchronization.

## R15

DO use graphics and effects to clarify the content. Every cutaway, zoom, transition, caption, or sound cue should have an editorial purpose.

## R16

DO NOT force every available capability into every video. A feature demonstration and a good audience-facing edit have different success criteria.

## R17

DO inspect visuals for meaning as well as appearance. Check that diagrams, screenshots, generated images, labels, cursor movements, and highlighted controls actually support the spoken claim.

## R18

DO NOT present simulated screens or generated imagery as recordings of real events, results, or performance. Make illustrative material distinguishable where confusion is possible.

## R19

DO maintain visual continuity and readability. Check typography, colors, subject identity, composition, contrast, crop boundaries, and text size at the intended viewing size.

## R20

DO use proven providers within their tested limits. Respect memory budgets, supported dimensions, reference limits, and concurrency constraints; do not silently substitute an unqualified capability.

## R21

DO NOT treat a successful request, installed model, or completed process as proof of usable output. Validate the returned artifact, reject incomplete responses, and inspect generated media before incorporating it.

## R22

DO use assets with documented provenance and appropriate permission. Keep prompts, references, model versions, and licensing information with the project; obtain scoped approval for hosted generation.

## R23

DO keep narration intelligible throughout the mix. Review music and effects beneath speech, inspect transitions, and measure final loudness and true peak.

## R24

DO validate the actual delivery files. Decode them, check dimensions and frame counts, verify audio duration, and confirm that captions and stems align—including inserted silence.

## R25

DO review the complete final video at normal playback speed with audio. Representative frames and automated checks supplement this review; they do not replace it.

## R26

DO NOT declare unavailable review steps complete. Distinguish technical validation, visual inspection, listening review, and user acceptance, with unresolved findings clearly identified.

## R27

DO reframe alternate formats deliberately. Preserve essential context, faces, demonstrations, and readable captions instead of relying on an automatic center crop.

## R28

DO make titles, thumbnails, and descriptions accurately represent the finished edit. Do not promise an outcome or demonstration the video does not deliver.

## R29

DO fix the underlying cause of a failed check and revalidate the affected outputs. Preserve successful versions, invalidate stale caches, and add regression coverage for reusable pipeline defects.

## R30

DO NOT consider the existing-video workflow qualified until it passes a representative real-footage edit. That next test must include authentic speech, meaningful editorial cuts, visible synchronization, selective graphics, and full audiovisual review.

## R31

DO NOT publish automatically when editing is complete. Publication requires approval of the actual deliverable and destination.
