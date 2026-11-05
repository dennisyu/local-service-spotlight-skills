# Publish packet: the Audit Factory write-up

Two pieces go live on blitzmetrics.com, in this order, from the files in this folder at the
commit you were handed. Publishing through the site's normal edit path is the publisher's job;
nothing here needs a person to copy text by hand.

## 1. The meta article (publish first; the section links to it)

| Field | Value |
|---|---|
| Source | `meta-article.html` (the comment at the top carries the fields below) |
| Title | How Cheaper Models Now Write Our 20-Page Audits |
| Slug | `/cheaper-models-write-our-audits/` |
| Author · category | Dennis Yu · meta articles |
| SEO title | How Cheaper Models Now Write Our 20-Page Audits, With Receipts |
| Meta description | One all-Claude 20-page audit cost $281 in AI fees. A cheaper model now writes the pages from finished research for about $1 to $2 in estimated fees, and Claude reviews. Every receipt, and what is still unproven. |
| Featured image | `img/demo-page-01.png` (page 1 of the kit's made-up demo audit) |
| Real photo | one approved photo from the media library (Dennis teaching, or the team at work), marked `data-lss-real-image="verified"`; the page has no other photograph |

## 2. The new How We Audit section

| Field | Value |
|---|---|
| Source | `how-we-audit-section.html` |
| Page | https://blitzmetrics.com/how-we-audit/ (post 112500) |
| Where | a new H2 directly after "How do you run a business strategy audit with your agent?" and before "Several exams; no blended score"; keep every other section as it is |
| Note | the live page has no declared real photo today (`fleet_check` flags it before this change); add an approved one while you are there if the media library has it |

## Images

Upload all four from `img/` and replace the `src` and `srcset` values:
`cost-per-audit.png` (1760×920, desktop chart), `cost-per-audit-phone.png` (900×1280, the
`<source>` inside `<picture>` for screens under 600px), `demo-page-01.png`, `demo-page-02.png`.
Both charts are drawn by `make_chart.py` from the kit's cost model; if a price changes, re-run it
rather than editing a picture.

## Link audit

Every outbound link in the two files, its class and its job. A link that is not on this table
and appears on the rendered page fails the closeout.

| Link | Class | Role | Verdict |
|---|---|---|---|
| https://blitzmetrics.com/how-we-audit/ | ours | concept: "our audit standard"; recipe row in the work record | keep |
| https://blitzmetrics.com/cheaper-models-write-our-audits/ | ours | the meta article, from the section | keep (live after step 1) |
| https://dennisyu.com/ | ours (person's own site) | first mention of Dennis Yu | keep |
| https://github.com/dennisyu/local-service-spotlight-skills/tree/main/audit-factory | ours | the deliverable: the kit | keep |
| https://github.com/dennisyu/local-service-spotlight-skills/pull/108 | ours | proof: full history and checks | keep |
| https://github.com/dennisyu/local-service-spotlight-skills/blob/main/audit-factory/docs/CALIBRATION.md | ours | proof: the measurements | keep |
| https://openrouter.ai/ | provider | execution step only: "create a key at openrouter.ai" | keep; every other mention of OpenRouter is plain text |
| https://openrouter.ai/docs/faq#pricing-and-fees | provider | support for one sourced claim: OpenRouter charges a fee when you buy credits | keep, labeled "OpenRouter's pricing FAQ" |

## Verify before calling it live

1. Fetch both public URLs anonymously, cache-busted: HTTP 200, and the page contains
   "How Cheaper Models Now Write Our 20-Page Audits" (meta article) or
   "Have cheaper models write the 20-page report" (How We Audit).
2. Run `python3 scripts/fleet_check.py <url> --tag article` on both live URLs. The fragments in
   this folder fail only on things the live page supplies: the site's analytics tag, the real
   photo, and the meta article's URL before step 1.
3. List the rendered page's external links and compare them with the table above.
4. Look at both pages at 1280×800 and 390×844: the chart is readable, nothing scrolls sideways,
   and the phone shows the tall chart.
5. Record both URLs and what you saw where the work was handed to you.
