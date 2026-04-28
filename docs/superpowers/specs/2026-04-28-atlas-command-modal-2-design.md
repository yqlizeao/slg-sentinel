# Atlas Command Modal 2.0 Design

## Goal

Polish every secondary navigation surface into a compact War Atlas-style command modal. The user should feel that each secondary panel is a designed product surface, not a Streamlit form or a page jump.

## Direction

Use the existing Streamlit runtime and `st.dialog` behavior, but make the visible modal system shared and disciplined:

- Secondary navigation opens a floating overlay over the current one-page stage.
- The browser URL should not change when a secondary panel opens.
- The modal is compact, centered, dark, and internally scrollable.
- Header, filter strip, metrics, visual rows, native controls, and footer use one shared Atlas visual language.
- Native Streamlit widgets remain functional, but are visually contained in Atlas slots.

## Modal Shell

- Width: `min(1080px, calc(100vw - 96px))` on desktop, with a mobile width below 390px.
- Height: `calc(100dvh - 120px)` maximum.
- Background: near-black layered panel using `rgba(12,15,20,.97)` and a subtle top highlight.
- Border: one-pixel low-contrast gold-gray border with a slightly brighter inner line.
- Radius: 14px for the shell, 6-8px for internal cards.
- Overlay: dim and blur the underlying Atlas stage, keeping it visible.
- Scroll: only the modal inner content scrolls; the document remains fixed.

## Internal Rhythm

Every command modal follows:

1. Compact header: icon, title, short subtitle, close button.
2. Thin filter/status strip: 2-4 low-height cells.
3. Compact metrics: 2-4 small cards with Cinzel values and mono labels.
4. Main analytical content: bar rows, segment rows, ranked lists, or compact native control sections.
5. Native slot: Streamlit form controls inside an Atlas container when editing is required.
6. Sticky footer: muted note on the left and compact actions on the right.

## Component Rules

- Do not render large full-width buttons inside modals.
- Do not put raw `st.dataframe` or Glide tables in the first visual position.
- Keep typography small and deliberate: display titles around 20-22px, body around 12-14px, labels around 9-11px.
- Use `Cinzel` only for titles and major numbers; use `IBM Plex Sans` and `IBM Plex Mono` for controls and labels.
- Use bar rows and segment rows to create War Atlas-like statistical texture.
- Avoid duplicated content: if data appears in the filter strip, do not repeat it in a large metric card unless it is a primary decision point.

## Page-Specific Intent

- Overview panels: read-only intelligence statistics, distribution, freshness, and ranked comments.
- Crawl panels: collection route cockpit, keyword library, field coverage, latest run result.
- Recursive panels: topic-map control surface, seed library, depth settings, candidate rows, run history.
- Profile panels: cohort filters, behavior tags, player detail, audience segment rows.
- Report panels: generated brief, insight ranking, sentiment mix, report actions.
- Competitor panels: side selection, metric duel, difference rows, comparison output.
- Settings panels: compact config matrix, targets, secrets, history, save status.

## Verification

- Py compile app and UI modules.
- Playwright desktop and mobile smoke:
  - secondary nav opens modal without changing URL;
  - modal floats over current page;
  - close button dismisses;
  - no document vertical scrollbar;
  - modal content scrolls internally when long.
- Run focused test suite available in `tests`.
