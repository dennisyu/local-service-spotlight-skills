# Measurement source contracts

Use this when connecting a client, choosing API versus export, or reconciling two
systems that report different numbers.

## Metric definitions

| Metric | Definition | Do not substitute |
|---|---|---|
| GBP call clicks | Clicks on the profile's call control | Connected calls, answered calls, or leads |
| Connected calls | Calls recorded by the call-tracking/phone system | GBP call clicks |
| Lead | Unique CRM contact meeting the client's written lead rule | Every new contact or spam submission |
| Qualified lead | Lead passing service, location, and intent rules | An open opportunity with no qualification receipt |
| Booking | Appointment or estimate with a stable CRM/calendar ID | Form submit or requested callback |
| Sale | Won opportunity/payment with a stable source record | Pipeline value or forecast |
| Revenue | Collected or recognized revenue, labeled explicitly | Opportunity value |
| Search performance | Search Console clicks, impressions, CTR, and position for the owned property | Third-party rank estimate |
| External rank | Vendor, query, location, device, and observed position | Search Console average position |

## Supported-source matrix

| Need | Preferred source | Contract |
|---|---|---|
| GBP visibility and intent | Google Business Profile Performance API | Daily impressions, `CALL_CLICKS`, direction requests, website clicks; monthly search-keyword impressions |
| Website acquisition | GA4 Data API | Sessions/users/events by source and landing page; keep property timezone |
| Owned-search results | Search Console Search Analytics API | Query/page/country/device rows; store requested range and response freshness |
| CRM leads and pipeline | HighLevel REST API or verified connector | Contacts, opportunities, appointments, payments, and conversations only when the selected scopes expose them |
| Page/funnel traffic | GA4 and ad landing-page data | Do not claim HighLevel's generic connector supplies page statistics without enumerating and testing the exact tool/endpoint |
| Paid media | Google Ads API / Meta Marketing API | Spend, clicks, conversions, conversion value; preserve account attribution settings |
| Competitive/local rankings | DataForSEO or another named SERP vendor | Store vendor, query, location, language, device, depth, URL, and observation time |
| Actual phone outcomes | Call-tracking or phone provider | Stable call ID, source, connected/answered status, duration, disposition |

Official references:

- Google Business Profile Performance API:
  `https://developers.google.com/my-business/reference/performance/rpc/google.mybusiness.performance.v1`
- GA4 Data API:
  `https://developers.google.com/analytics/devguides/reporting/data/v1`
- Search Console Search Analytics API:
  `https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
- HighLevel APIs and Private Integrations:
  `https://marketplace.gohighlevel.com/docs/`
- Google Ads reporting:
  `https://developers.google.com/google-ads/api/docs/reporting/overview`

## Normalized row

Store one immutable row per metric, source, client, and period:

```json
{
  "client_id": "stable-client-id",
  "source": "gbp-performance",
  "account_id": "stable-source-account",
  "metric": "gbp_call_clicks",
  "period_start": "2026-07-27",
  "period_end": "2026-08-02",
  "timezone": "America/New_York",
  "value": 17,
  "unit": "count",
  "scope": {"location_id": "123"},
  "collected_at": "2026-08-03T11:05:00Z",
  "run_id": "maa-2026w31-client-id",
  "source_record_id": null,
  "status": "observed"
}
```

Never overwrite raw rows. Correct them with a superseding row and reason so an
auditor can reconstruct the report.

## Connection tiers

1. **API/webhook:** scheduled, scoped, reproducible, and monitored.
2. **Scheduled export:** a platform drops a CSV into a controlled folder.
3. **Manual export:** acceptable for a pilot; record who exported it and when.
4. **Not connected:** explicit gap. Never estimate it into the report.

Use API-first only when the endpoint has been tested for the required metric. A
reliable CSV is better than an imagined API capability.

## QA before MAA

- Assert every required client/source combination produced a success or failure
  receipt; absence is a missing run.
- Check timezone, inclusive/exclusive period boundaries, source latency, units,
  duplicate source IDs, negative values, and >30% changes.
- Re-pull one prior period with the current configuration when a movement is
  surprising; configuration drift can imitate business change.
- Keep GBP call clicks, tracked calls, leads, bookings, and sales separate through
  normalization. Join them only with stable IDs or an explicit attribution rule.
- Compare rankings only under the same vendor, query, location, language, device,
  and depth. Report cross-vendor disagreement rather than averaging it away.
- Produce the MAA report only after QA passes or with the failed assertions visibly
  attached.
