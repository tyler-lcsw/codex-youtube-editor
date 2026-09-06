# How to Use Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Comprehensive, simple, searchable end-user help integrated into Codex Media Studio.
**Architecture:** One JSON guide feeds native SwiftUI help and a static HTML export. Per-tab help uses a sheet so reading instructions does not discard a draft. A validated loader uses repository content with bundled fallback.
**Tech Stack:** SwiftUI, Foundation Codable, Python standard library, existing app bundle builder.
**Spec:** plan/How to Use — Specification.md

## Global Constraints
- Preserve all existing projects, credentials, media and production rules.
- No new network dependency, API fallback, publication testing, implicit downloads or unsupported capability claims.
- End-user instructions use current visible control labels and plain numbered steps.
- JSON source schema is fixed by the specification; extras may be ignored but unsupported versions rejected.

## Task 1: Author and audit the guide
Files: create docs/user-guide.json and docs/help-coverage.md.
Interface: schema_version/title/articles; article id/section/title/summary/status/steps/notes/prompt as specified.
- [x] Read all five views, Workspace, workflow routes/stages, all 18 skills and current provider/qualification docs.
- [x] Write complete plain-language articles and record every control/option/skill to article-ID coverage.
- [x] Explain missing features and raw-footage qualification honestly; no fictional buttons or auto-save promises.
- [x] Parse JSON and self-review every instruction against implementation. Review content separately.

## Task 2: Add native help
Files: create macos/Sources/StudioCore/HelpGuide.swift, macos/Sources/Studio/HelpView.swift and macos/Tests/StudioCoreTests/HelpTests.swift; modify StudioApp.swift, StudioTheme.swift, native test runner and tools/build_studio_app.py.
Interface: public Codable guide/article types; validated source loading with source label/fallback reason; public filtering by section/query. HelpView takes engine:String and initialSection:String?; context sheet does not mutate the underlying tab.
- [x] Write failing tests for invalid IDs/version, section-plus-full-text filtering and missing/invalid repository fallback to bundle.
- [x] Implement minimal decoder and filtering; run native checks.
- [x] Render search, section picker, numbered articles, status/notes, Copy example and Reload help. Missing guide shows actionable error.
- [x] Add How to Use sidebar/menu and Help for this tab sheet with Done. Bundle the authoritative JSON.
- [x] Build app and review code. Preserve existing authentication and AVPlayer ownership.

## Task 3: Export, test and close out
Files: create tools/build_user_guide.py and tests/test_user_guide.py; generate docs/how-to-use.html; update user-facing entry docs/status. Parent assesses tutorial storyboard after content complete.
Interface: render_guide(data:dict)->str validates and HTML-escapes text; main writes docs/how-to-use.html from docs/user-guide.json; standalone anchors use article IDs.
- [x] Write failing tests for escaped text, complete article rendering and bundled guide preservation.
- [x] Implement standalone accessible HTML with TOC, search, print styling and no remote dependencies.
- [x] Cross-check source coverage, generated export and guide usability; document tutorial feasibility/storyboard.
- [x] Verify native empty-project help, contextual sheet, search/copy/reload and existing tab access. Run focused/full tests as warranted, excluding publication.
- [x] Review whole branch, commit/push/merge under standing authorization, install and verify final app.
