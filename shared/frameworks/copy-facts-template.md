# Copy Facts Template (the fact sheet)

One file per client, `compiled/copy-facts.md` (BlitzBase) or
`{Client}_CopyFacts.md` (simple mode). The copy optimizer may not put a claim in
an ad unless it is on this sheet. Built from the client's own website and
Google Business Profile; refreshed when older than 30 days, when the site is
rebuilt, or when a live-ad fact check finds a contradiction.

Rules:
- One claim per line, quoted or closely paraphrased, with the URL and the date read.
- Never an inference. If the site is silent, write "not stated".
- Record what the business does NOT do as carefully as what it does.
- Review rating and count come from the Google Business Profile, dated; they go stale fastest.
- When the client tells us something the site does not say, it goes in with
  source "client, {date}, {channel}" and stays until the site agrees or the
  client corrects it.

```
# {Client} - Copy Facts
> Last full read YYYY-MM-DD. Sources: {domain}, Google Business Profile.

## Services and products offered
- {claim} | {URL} | {date}

## NOT offered / explicitly excluded
- {claim} | {URL} | {date}

## Service area
- {claim, by county or city as the site states it} | {URL} | {date}

## Pricing
- {pricing model, published prices, fees included or excluded} | {URL} | {date}

## Timing and logistics promises
- {same-day, delivery windows, rental periods} | {URL} | {date}

## Proof
- Google rating {x.x}, {n} reviews | GBP | {date}
- {years in business, licensing, awards, as stated} | {URL} | {date}

## Page language (one block per final URL in use)
### {final URL}
- H1: "{text}"
- Main headings: "{text}"; "{text}"
- CTA wording: "{text}"
- Service terms the page uses: {terms}
- Conflicts with the ad group that points here: {e.g. "No Long-Term Contracts. Ever." on the page the Long-Term ad group uses}
- Status: {200 / redirects to X} | {date}
```
