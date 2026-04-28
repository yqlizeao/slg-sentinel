# Atlas Command Modal 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish all secondary navigation panels into compact War Atlas-style command modals.

**Architecture:** Keep Streamlit as runtime and `st.dialog` as the overlay primitive. Centralize modal structure in `ui/components/atlas_shell.py`, then refine global modal CSS in `app.py` and wrap native Streamlit controls in explicit Atlas slots.

**Tech Stack:** Python, Streamlit, HTML string helpers, CSS, Playwright smoke scripts.

---

### Task 1: Tighten Shared Modal Primitives

**Files:**
- Modify: `ui/components/atlas_shell.py`

- [ ] Add `render_atlas_native_slot(title, body_html="", caption="")` for visual wrapping around native controls.
- [ ] Add optional `tone`, `size`, and `footer_actions` fields to `render_atlas_command_modal`.
- [ ] Keep session-state secondary navigation so panel opens do not change the URL.
- [ ] Remove legacy popover helper usage from page code.

### Task 2: Refine Modal CSS System

**Files:**
- Modify: `app.py`

- [ ] Reduce dialog width to `min(1080px, calc(100vw - 96px))`.
- [ ] Reduce header, metric, filter, and footer heights.
- [ ] Restyle native Streamlit controls inside dialogs to match Atlas controls.
- [ ] Style `.atlas-native-slot` as the only visible container for edit controls.
- [ ] Keep hover states subtle and remove motion.

### Task 3: Recompose Crawl And Recursive Modal Bodies

**Files:**
- Modify: `ui/pages/crawl.py`
- Modify: `ui/pages/recursive_crawl.py`

- [ ] Make route/config panels decision-first: compact metrics, bars, then native controls.
- [ ] Move keyword libraries into compact native slots.
- [ ] Replace repeated explanatory blocks with one-line footer notes.
- [ ] Keep keyword persistence and recursive config behavior unchanged.

### Task 4: Apply Same Modal Grammar To Remaining Pages

**Files:**
- Modify: `ui/pages/overview.py`
- Modify: `ui/pages/profile.py`
- Modify: `ui/pages/report.py`
- Modify: `ui/pages/competitor.py`
- Modify: `ui/pages/settings.py`

- [ ] Remove oversized metric sections where content is repeated.
- [ ] Prefer bar rows, segment bars, and compact list editors.
- [ ] Wrap settings and form-like controls in Atlas native slots.
- [ ] Preserve existing service APIs and persistence formats.

### Task 5: Verify

**Files:**
- Run only commands; no file edits expected.

- [ ] Run `python3 -m py_compile app.py ui/components/*.py ui/pages/*.py`.
- [ ] Run TOML locale parse.
- [ ] Run Playwright desktop and mobile modal smoke checks.
- [ ] Run `python3 -m pytest -q tests`.
