---
{
  "title": "The Nine Triangles do not drift — corners and order are canonical",
  "severity": "warn",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04: 'our nine triangles first principles need to propagate cleanly ... come in and fix and garbage collect and prevent stuff from drifting.'",
  "source": "https://blitzmetrics.com/9-triangles-framework-scalable-home-service-businesses/",
  "applies_to": ["published-html", "agent-behaviour"],
  "checks": [
    {
      "id": "ccs-order-not-inverted",
      "kind": "forbid_regex",
      "pattern": "Checklist\\s*(?:→|-&gt;|->|,|·)\\s*Content\\s*(?:→|-&gt;|->|,|·)\\s*Software",
      "message": "CCS is Content · Checklist · Software; a 'Checklist -> Content -> Software' ordering is the inverted acronym and is framework drift",
      "examples": {
        "violating": [
          "The order is Checklist → Content → Software.",
          "CCS runs Checklist -> Content -> Software."
        ],
        "clean": [
          "CCS runs Content → Checklist → Software: experiment, codify, automate.",
          "Content · Checklist · Software — content first, because you cannot checklist what you have not discovered."
        ]
      }
    },
    {
      "id": "legacy-alias-acc-as-current",
      "kind": "forbid_regex",
      "pattern": "Awareness\\s*(?:→|-&gt;|->|·|,)\\s*Consideration\\s*(?:→|-&gt;|->|·|,)\\s*Conversion",
      "message": "ACC (Awareness/Consideration/Conversion) is the legacy funnel alias; the current triangle is AEC (Audience/Engagement/Conversion). Present the legacy corners only as disclosed lineage",
      "examples": {
        "violating": [
          "Our funnel triangle is Awareness · Consideration · Conversion.",
          "The AEC funnel: Awareness -> Consideration -> Conversion."
        ],
        "clean": [
          "AEC — Audience · Engagement · Conversion (legacy alias ACC, disclosed).",
          "The funnel triangle is Audience · Engagement · Conversion."
        ]
      }
    },
    {
      "id": "legacy-alias-abp-as-current",
      "kind": "forbid_regex",
      "pattern": "Analyst\\s*(?:→|-&gt;|->|·|,)\\s*Business\\s*(?:→|-&gt;|->|·|,)\\s*Partner",
      "message": "ABP (Analyst/Business/Partner) is historical; the current mission triangle is SBP (Specialist/Business/Partner). Present the legacy corners only as disclosed lineage",
      "examples": {
        "violating": [
          "The mission triangle is Analyst · Business · Partner.",
          "Our SBP is Analyst -> Business -> Partner."
        ],
        "clean": [
          "SBP — Specialist · Business · Partner (ABP retained only for lineage).",
          "The mission triangle is Specialist · Business · Partner."
        ]
      }
    }
  ]
}
---

## The Nine Triangles do not drift

- **Corners and order are canonical** (`nine-triangles/references/canonical-framework.md`,
  version 2026-08-06, owner-accepted 2026-08-09). A copied pack, an article, or a shared rule
  that reorders a triangle or presents a legacy alias as current is **drift**, and drift is
  how one wrong copy becomes everyone's default.
- **Order is meaning.** CCS runs Content, then Checklist, then Software (experiment, then
  codify, then automate — you cannot checklist what you have not discovered). GCT runs Goals,
  then Content, then Targeting. Reordering a triangle changes the claim; it is not a stylistic
  choice.
- **Legacy aliases are aliases.** ACC to AEC and ABP to SBP may appear only when explaining
  lineage, and only with the drift disclosed. Never present the legacy corners as the current
  operating name.
- **When you find drift, fix it at the source.** Correct the `standards/` file or the
  canonical article, run `sync_shared_rules.py`, and note the reconciliation — do not patch one
  downstream copy and leave the others. (This is the general form of the 2026-09-04 CCS fix:
  `capture-what-you-learn` carried the inverted ordering; it was corrected there, not in the
  artifact that happened to quote it.)
- **The check reports; a human confirms.** A regex cannot tell disclosed lineage from live
  drift, so a hit is "look here," not "block" — hence `severity: warn`. Preserve the reason
  when a hit is cleared as legitimate. Pair with `congruency-audit` for master-vs-skin
  reconciliation and `skill-registry` when a copied pack needs reconciling to canon.
