# HP Research Note Insertion Plan

## Purpose

Define how World Pulse can introduce a lightweight public Research Note without overclaiming or changing the core public product.

## Current Public Site Role

- `index.html`: daily observation entry. It should remain focused on Signal Position, data date, observation cards, and source notes.
- `about.html`: product explanation. It explains what World Pulse is, who it helps, boundaries, data window, and sources.
- `framework.html`: methodological explanation. It explains the Reality-Reflection structure, source layers, calibration principles, and limitations.
- `brief.html`: pull-based subscription interest. It collects interest in a weekly note without external form integration.
- `contact.html`: custom observation / research contact. It supports questions about source windows, source-linked datasets, and research use.

## Current Strategic Boundary

From `docs/current_strategy_index.md`:

- Product definition: Reality-Reflection Observatory
- Strongest internal category: Historical Space Weather
- Commercial hypothesis: AI/RAG reference-data freshness review
- Buyer-facing proof: not yet
- Public marketing claim: not yet

## Proposed Public Addition

Recommendation: add `public/reference-data-freshness.html`, but keep it lightweight and research-note framed.

Why:

- The concept is now mature enough for a careful public research note.
- The private briefing itself should remain private.
- A separate page avoids overloading the daily `index.html` or turning `about.html` into a method memo.
- The page can support pull-based evaluation from X ads without changing the core public product.

Why not put it directly on the homepage:

- The homepage should stay a daily observation entry.
- The AI/RAG hypothesis is still not buyer-facing proof.
- Putting the idea on the homepage could make the public product look broader than the current evidence status.

## What the New Page Should Do

- Introduce reference-data freshness review as a research note.
- Explain the idea lightly.
- Link to `/contact.html`.
- Link to `/framework.html` for method context.
- Avoid publishing private briefing details.
- Avoid product proof language.
- State that the current evidence is internal and exploratory.
- Keep Historical Space Weather as an example category without exposing the full private deck.

## What Existing Pages Should Change

### `index.html`

Recommendation: no change at first.

Rationale: the homepage should remain a stable daily observation entry. Adding AI/RAG language there could blur the public product.

### `about.html`

Recommendation: small contextual link only.

Rationale: About already describes who uses World Pulse and what it helps with. A single link such as "Research note: reference-data freshness" can sit near Next Steps after the page exists.

### `framework.html`

Recommendation: small contextual link.

Rationale: Framework is the most natural place to link the Research Note because it already explains Reality-Reflection, reflection signals, and limitations.

### `brief.html`

Recommendation: no change at first.

Rationale: Brief should stay focused on weekly notes and not become the AI/RAG landing page.

### `contact.html`

Recommendation: small wording addition only after the Research Note exists.

Rationale: Contact can mention questions about reference-data freshness review, but should not become sales copy.

## Recommended Navigation

Recommended placement: About/Framework contextual link plus footer link.

Do not add it as a primary main nav item yet.

Reason:

- Main nav should stay simple: Latest, About, Framework, Brief, Contact.
- Research Note is exploratory and should not look like a core public product.
- Footer/contextual links are enough for pull-based testing.

## X Ads Landing Page Recommendation

Preferred landing page after the note exists: `public/reference-data-freshness.html`.

Reason:

- `index.html` is too focused on daily observation and may not explain the AI/RAG hypothesis.
- `about.html` is broad and may require too much scanning.
- A dedicated Research Note can set boundaries, explain the idea, and route interested readers to Contact.

Before the Research Note exists, use `about.html` rather than `index.html`.

## Copy Risk Review

Avoid phrases or framing that imply:

- AI/RAG product proof
- Model diagnosis
- Real-time attention
- Prediction
- Emergency or action relevance
- Market relevance
- Public Gap display
- Completed product validation

Safer framing:

- Research note
- Reference-data freshness review
- Source-linked examples
- Structured reference-system activity
- Internal evidence, not public proof
- Private briefing remains private

## Recommended Next Step

Choice: **(a) create Research Note page now**

Conditions:

- Keep it lightweight.
- Do not expose private briefing content.
- Do not add it to primary nav yet.
- Link it from Framework and footer after review.
- Use it as the preferred X ads landing page only after copy review.

## Proposed Page Outline

Suggested title: `Reference-Data Freshness Research Note`

Suggested sections:

- What this note is
- What World Pulse reviews
- Why reference-data freshness may matter for AI/RAG
- Current internal evidence status
- Why Historical Space Weather is currently useful internally
- What this note does not claim
- Contact for research use

Evidence language should stay short and avoid detailed private briefing tables.

## Implementation Order

1. Draft `public/reference-data-freshness.html` in a separate task.
2. Run forbidden wording check.
3. Review with `docs/current_strategy_index.md` as the strategic anchor.
4. Add contextual links from `framework.html` and `about.html` only after the page copy is approved.
5. Add footer link only if the page remains clearly research-note framed.
6. Consider X ads only after one manual copy review.
