# Stage 30 — Identity gate

Nothing downstream can repair a wrong identity, so this stage decides whether the audit may
attribute anything at all.

## Rule

CONFIRMED needs **two independent attributes**, each from a different source origin: a
registry or license, an employer or company page, a matching handle, a location plus role
chronology, a co-founder, an institution, a dated media appearance. A matching name is not an
attribute. One attribute is a hypothesis. Same-photo matching is not used.

## Output (JSON)

```json
{"identity": {
  "status": "CONFIRMED",
  "attributes": [
    {"attribute": "State roofing registration: Vega Roofing LLC, Tulsa, active", "evidence": ["V-E002"]},
    {"attribute": "Chamber directory names Marisol Vega as owner at the same address", "evidence": ["V-E003"]}
  ],
  "namesakes": ["Marisol Vega, Miami realtor", "Marisol Vega, actress"],
  "qualifier": "Marisol Vega, Tulsa roofer",
  "notes": "bare name lost to namesakes #1-#6; qualified name resolves #1-#3"}}
```

If you cannot reach two attributes, set `status: "HOLD"`, list what you tried, and stop the
scoring stage; the report may still be written as INCOMPLETE with no numbers. On HOLD the
renderer hatches all ten Brand Authority rows and leaves the score box empty, and gate G54 fails
any Brand Authority score typed as `N/100` in the text, so write no number (not even a
subtotal) until identity is CONFIRMED.

## Also decide

For every person or organization you will draw on the connections page: the public
association type (host, guest, colleague, co-presenter, sponsor, co-presence) with a dated
source, and `depth: "UNKNOWN"` unless a direct record proves closeness. Co-presence is never
friendship, endorsement or permission.
