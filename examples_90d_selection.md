# Sales Sample Candidate Audit (Internal)

## Purpose

Evaluate whether current 90-day examples can be presented to prospective buyers.

This is a kill criteria document, not a sales deck. The question is whether the current Reality-Reflection examples can survive a direct "so what?" review from teams evaluating AI/RAG, reference-data freshness, insurance research, data journalism, or academic use.

## Kill Criteria

If none of the 3 candidates can withstand "so what?", current methodology is insufficient and Phase 2 entity linking is required.

## Candidate 1: 2026-05-20

### Reality observations

- Signal Position: 95
- Reality Position: 98
- Reflection Position: 30
- Reality-Reflection difference: 68
- Reality raw score: 53.40
- Top reality observations:
  - M6.6 earthquake near southern East Pacific Rise, observed 2026-05-20 17:43 UTC.
  - M5.9 earthquake near 10 km NNW of China, Japan, observed 2026-05-20 02:46 UTC.
  - M5.9 earthquake near 8 km E of Wadomari, Japan, observed 2026-05-20 02:46 UTC.

### Reflection observations

- No reflection-layer observation was available in stored Wikipedia top pages for this data date.
- Core targeted reflection pages: none found in stored Wikipedia top pages.
- Context targeted reflection pages: none found in stored Wikipedia top pages.
- Reflection raw score: 0.
- Reflection raw score topic pages: 0.

### What we can say

- The tracked reality layer was high relative to the recent window.
- The stored Wikipedia reflection layer did not show matching top-page reflection for this data date.
- This is a clean example of a measurable separation between observed reality records and the current Wikipedia reflection proxy.

### What we cannot say

- We cannot say the events were absent from public awareness.
- We cannot say other sources, search systems, news, or apps did not reflect the events.
- We cannot say this is event-level reference freshness without entity linking from reality events to reference pages.
- We cannot claim the Wikipedia layer should have reflected these events on the same date.

### Buyer reaction simulation

- Likely positive: "This is easy to understand as a source freshness test."
- Likely concern: "Why is Wikipedia the reflection source for an earthquake sequence?"
- Likely follow-up: "Can you link the earthquake location and event type to candidate reference pages automatically?"

### Suitability by buyer type

- AI/RAG: Medium. Good for explaining why reference freshness checks matter, but needs entity linking before it is operational.
- Insurance/risk research: Medium. Strong reality signal, but reflection evidence is mainly absence in the stored proxy.
- Data journalism: Medium-low. Useful as a lead for background review, but not enough by itself for a story example.
- Academic/policy: Medium. Good as a methodology stress test.

## Candidate 2: 2026-05-14

### Reality observations

- Signal Position: 88
- Reality Position: 95
- Reflection Position: 30
- Reality-Reflection difference: 65
- Reality raw score: 25.63
- Top reality observations:
  - M6.2 earthquake near 271 km WSW of Tual, Indonesia, observed 2026-05-14 17:53 UTC.
  - M5.3 earthquake near 32 km WNW of Darien, Colombia, observed 2026-05-14 12:48 UTC.
  - M5.2 earthquake near Volcano Islands, Japan region, observed 2026-05-14 15:34 UTC.

### Reflection observations

- Global topic reflection top page: Wes_Streeting.
- Total topic views: 17636657.
- Core targeted reflection pages: none found in stored Wikipedia top pages.
- Context targeted reflection pages:
  - Japan, 12454 views.
  - Turkey, 9130 views.
- Reflection raw score targeted context: 21584.

### What we can say

- The reality layer was high, while broad Wikipedia topic reflection did not align with the observed geophysical events.
- Some context pages appeared, but they are broad country pages and should not be treated as direct event reflection.
- This candidate shows why core and context targeted reflection must be separated.

### What we cannot say

- We cannot say the context page views were caused by the listed earthquakes.
- We cannot say the global topic page is relevant to the reality observations.
- We cannot use this as a buyer-facing example without explaining that current targeted context is weak evidence.
- We cannot present country-page traffic as event-level reference movement.

### Buyer reaction simulation

- Likely positive: "The system separates reality records from broad reference traffic."
- Likely concern: "Japan and Turkey are too broad to be persuasive."
- Likely follow-up: "Can you match locations, event names, and category pages more precisely?"

### Suitability by buyer type

- AI/RAG: Medium-low. Demonstrates the need for reference-data review, but entity linking is needed.
- Insurance/risk research: Medium. Useful for selected-region monitoring, but not a strong standalone sample.
- Data journalism: Low. The reflection side is too generic.
- Academic/policy: Medium. Useful for explaining limitations and calibration.

## Candidate 3: 2026-05-15

### Reality observations

- Signal Position: 92
- Reality Position: 95
- Reflection Position: 31
- Reality-Reflection difference: 64
- Reality raw score: 50.07
- Top reality observations:
  - M6.7 earthquake near 49 km ESE of Ofunato, Japan, observed 2026-05-15 11:22 UTC.
  - M5.4 earthquake near 119 km SSE of Lorengau, Papua New Guinea, observed 2026-05-15 01:13 UTC.
  - M4.9 earthquake near 11 km WNW of Palca, Peru, observed 2026-05-15 15:45 UTC.

### Reflection observations

- Global topic reflection top page: Iceman_(Drake_album).
- Total topic views: 17737360.
- Core targeted reflection pages: none found in stored Wikipedia top pages.
- Context targeted reflection pages:
  - Japan, 12394 views.
  - Turkey, 8996 views.
- Reflection raw score targeted context: 21390.

### What we can say

- The tracked reality layer was high, led by a large Japan-region earthquake.
- The global Wikipedia reflection stream was dominated by unrelated topic traffic.
- Context pages appeared, but they are not enough to support event-specific reflection.
- This is a clear demonstration that global topic reflection is not the same as targeted reference freshness.

### What we cannot say

- We cannot say Wikipedia failed to represent the specific earthquake without linked candidate pages.
- We cannot say Japan page traffic corresponds to the earthquake.
- We cannot say the global topic stream is useful for this buyer case without filtering and entity linking.
- We cannot present the reflection layer as event-level evidence yet.

### Buyer reaction simulation

- Likely positive: "This explains why global topic traffic is not enough."
- Likely concern: "The example proves the limitation more than the product value."
- Likely follow-up: "Can you connect this earthquake to Japan earthquake pages, regional pages, and source citations?"

### Suitability by buyer type

- AI/RAG: Medium. Strongest of the three for explaining reference-data freshness needs, but still requires entity linking.
- Insurance/risk research: Medium. Strong reality signal, weak reflection specificity.
- Data journalism: Medium-low. Could support a methods note, not a standalone sample.
- Academic/policy: Medium-high. Useful as a clean example of measurement limits.

## Verdict

### (a) sellable now

No.

The current examples are understandable, but not strong enough to present as finished buyer-facing proof. They demonstrate that Reality-Reflection separation exists in the current data model, but the reflection side is too coarse.

### (b) entity linking required

Yes.

Phase 2 entity linking is required before these examples can withstand a buyer "so what?" review. The system needs to connect reality observations to candidate reference pages by event type, location, source metadata, and topic families.

Minimum next step:

- Link earthquake events to candidate reference pages such as earthquake topic pages, regional earthquake pages, country or region pages, and source-citation targets.
- Separate direct event/topic pages from broad context pages.
- Report when no linked reference candidates appear in stored Wikipedia top pages.

### (c) deeper methodology issue

Not yet proven.

The current result does not invalidate the methodology. It shows that the reflection proxy is too broad without entity linking. If Phase 2 linking still produces weak or non-explanatory examples, then the methodology may need a different reflection source or a narrower buyer use case.
