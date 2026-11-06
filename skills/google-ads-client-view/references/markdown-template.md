<!--
STRUCTURAL TEMPLATE for the Google Ads Client View (markdown output).
Reuse the layout; replace every {{TOKEN}}. Charts embed as markdown images
pointing at the two PNGs in the same folder, so the .md previews with charts
inline. Project every section from the MAA per the SKILL.md source map. Do not
invent content the MAA does not contain. No em dashes.
-->

# {{CLIENT}}, Weekly Google Ads Report

**{{STATUS_DOT}} {{STATUS_LABEL}}** · Week of {{DATE_PRETTY}}

## The bottom line

> {{BOTTOM_LINE_PARAGRAPH}}

## 📊 The trend, last 13 weeks

![Leads per week]({{LEADS_PNG}})

![Cost per lead]({{CPL_PNG}})

## What's working ✅

{{WORKING_ITEMS, one "- ✅ ..." line per positive finding in Analysis}}

## What needs attention 🔴

{{ATTENTION_ITEMS, client-facing critical/decision items only, "- 🔴 **...**"}}

## 👉 What we need from you this week

{{CLIENT_ASKS, numbered list, one "**ask** + one-line why" per client-side Action}}

## What we did this week (no action needed)

{{WE_DID, one "- ✅ ..." line per our-side Action, phrased as done/in-progress}}

---

## Full analysis (for the detail-minded)

**Metrics**

**{{CAMPAIGN_NAME}} ({{CAMPAIGN_TYPE}} | {{BID_STRATEGY}})**

- **Cost**: {{COST}}
- **Impressions**: {{IMPRESSIONS}}
- **Clicks**: {{CLICKS}}
- **CTR**: {{CTR}}
- **CPC**: {{CPC}}
- **Conversions**: {{CONVERSIONS}}
- **CPA**: {{CPA}}

<!-- repeat the campaign block for each Search/PMax campaign in the MAA -->

{{ANALYSIS_PARAGRAPHS, verbatim from the MAA, including the CRM check}}

**Action**

{{ACTION_ITEMS, verbatim from the MAA, numbered}}

**Start here:** {{START_HERE, verbatim from the MAA}}
