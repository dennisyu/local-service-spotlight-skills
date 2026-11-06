---
name: google-ads-lp-auditor
description: >
  Audit Google Ads landing pages for ad-to-page alignment, conversion friction,
  and Landing Page Experience signals. Use this skill whenever the google-ads-analyzer
  identifies Below Average Landing Page Experience on any keyword, when a campaign
  shows strong CTR but poor conversion rate (suggesting post-click problems), when
  an MAA needs landing page recommendations, or when a user asks to review a landing
  page in the context of Google Ads performance. Also trigger on "review my landing
  page", "why is my LP Experience below average", "page isn't converting", "audit
  this URL for Google Ads", "what's wrong with my landing page", or any request to
  evaluate a landing page against the ads pointing to it. This skill produces
  findings formatted for insertion into an MAA, it is not a standalone website
  audit tool.
---

# Google Ads Landing Page Auditor

## What This Skill Does

This skill audits a landing page in the context of the Google Ads campaign
pointing to it. The output isn't a generic website review, it's a focused
assessment of whether the page is helping or hurting the ads' performance,
organized for direct insertion into an MAA document.

The skill answers three questions:
1. **Does the page match the ad's promise?** (ad-to-page intent alignment)
2. **Can visitors convert easily?** (friction analysis)
3. **What does Google see?** (technical LP Experience signals)

## When This Skill Gets Called

The google-ads-analyzer dispatches this skill when it detects:
- Below Average Landing Page Experience on any keyword with meaningful spend
- Strong CTR (>3%) paired with zero or near-zero conversions over 2+ weeks
- A pattern where ad copy promises don't match what the page delivers

The skill can also be invoked directly by a user who wants a landing page
reviewed in the context of their Google Ads data.

## Required Inputs

The skill needs these inputs to produce useful findings. When dispatched by the
analyzer, these come from the MAA data. When invoked directly, ask the user.

1. **Landing page URL**, the actual URL traffic is hitting (check final URLs
   in the ad data, not just the display URL)
2. **Ad copy**, the RSA headlines and descriptions currently running. These
   define what the visitor was promised before they clicked.
3. **QS component data**, specifically the Landing Page Experience rating and
   Ad Relevance rating for the top-spend keywords pointing to this page.
4. **Campaign context**, what the business sells, the target CPA, the
   conversion action (calls, forms, purchases), and who the audience is.

Optional but valuable:
- Conversion rate data (clicks vs conversions on this page)
- Whether the page has been changed recently
- CRM data on lead quality from this page

## Audit Framework

Work through these three layers in order. Each one builds on the last.

### Layer 1: Ad-to-Page Intent Match

This is the most common reason for Below Average LP Experience and poor
conversion rates. Google's LP Experience score explicitly factors in how well
the page matches the ad copy.

**Check the promise chain:**
- Read the RSA headlines and descriptions. What is the ad promising? A free
  estimate? Emergency service? A specific product at a specific price? A free
  audit?
- Load the page. What does the visitor see above the fold? Does it continue
  the conversation the ad started, or does it feel like a different topic?
- Look for the specific words from the ad copy on the page. If the ad says
  "Free Roof Inspection" and the page headline says "Premier Roofing
  Solutions," that's a disconnect Google can detect and visitors can feel.

**Common intent mismatches in local service businesses:**
- Ad promises a specific service, page is the homepage or a generic services
  page
- Ad promises "free estimate/audit/inspection," page leads with pricing or
  qualification requirements
- Ad uses geographic language ("Dallas Dumpster Rental"), page doesn't mention
  the city anywhere
- Ad emphasizes urgency ("Same-Day Service"), page has no urgency cues
- Ad targets one audience (e.g., adult children worried about aging parents),
  page speaks to a different audience (e.g., the seniors themselves)

**Scoring:**
- **Strong match**: Above-the-fold headline echoes the ad's primary promise,
  page content reinforces the ad's value proposition, visitor can see a path
  to the promised action immediately
- **Partial match**: Page is topically related but doesn't continue the ad's
  specific promise. Visitor has to work to connect the ad to the page.
- **Mismatch**: Ad promises one thing, page delivers another. This is the
  most common cause of Below Average LP Experience + poor conversion rate.

### Layer 2: Conversion Friction

Once you know whether the page matches the ad, assess how easy it is for a
motivated visitor to convert.

**Above the fold:**
- Is there a CTA visible without scrolling? On mobile?
- Does the CTA match the conversion action? (If the conversion is a phone
  call, is the phone number prominent? If it's a form, is the form visible
  or at least a button that jumps to it?)
- Is there a competing element that might distract from the CTA? (Popups,
  chat widgets, navigation menus that pull attention away)

**Form/conversion path:**
- How many fields? Every field above 3-4 reduces completion rate.
- Is the form asking for information that feels premature? (Revenue
  qualifiers, detailed project descriptions, before trust is built)
- Is the submit button clear and action-oriented? ("Get My Free Estimate"
  beats "Submit")

**Trust signals:**
- Social proof above the fold? (Testimonials, review counts, logos, results)
- If the service costs >$500 or is a recurring commitment, the page needs
  more trust-building than a simple drain cleaning page
- For unfamiliar brands arriving via paid ads, visitors need a reason to
  believe the company is real and competent

**Mobile experience:**
- Most local service traffic is mobile. The above-the-fold experience on a
  phone matters more than on desktop.
- Tap targets large enough? Phone number clickable?
- Content reflows sensibly or requires horizontal scrolling?

### Layer 3: Technical LP Experience Signals

Google's Landing Page Experience score is influenced by page speed, mobile
usability, and content relevance. This layer assesses the technical factors.

**PageSpeed / Core Web Vitals:**
- Use PageSpeed Insights data if available (the analyzer or user may provide
  this). Focus on:
  - **LCP (Largest Contentful Paint)**: >2.5s is a problem. Google considers
    this the primary loading metric.
  - **TBT/INP (Total Blocking Time / Interaction to Next Paint)**: High TBT
    means JavaScript is blocking the main thread, the page feels sluggish.
  - **CLS (Cumulative Layout Shift)**: Elements jumping around as the page
    loads erodes trust and usability.
- Lab scores matter more than field scores for LP Experience assessment.
  Google's ad quality system evaluates pages in a controlled environment
  closer to lab conditions.
- Common culprits for local service sites: unoptimized images, too many
  Shopify/WordPress plugins loading JavaScript, chat widgets, review widgets,
  and tracking scripts competing for resources.

**Content relevance signals:**
- Does the page contain the keywords that triggered the ads? Google's LP
  assessment checks for semantic relevance between the query, the ad, and
  the page content.
- Is the content substantial enough? Thin pages with mostly images and a
  form may not provide enough text signal for Google to evaluate relevance.
- Is there duplicate content across multiple landing pages? (Common when
  businesses create city-specific pages with only the city name changed)

**Indexing and crawlability:**
- Is the page noindexed? Google can still land ads on noindexed pages, but
  it may affect how the quality system evaluates the page.
- Any redirects between the ad's final URL and what the visitor sees?
  Redirect chains add latency and can create URL mismatches.

## Output Format

The skill produces two outputs, both formatted for MAA insertion:

### 1. Analysis Insert (1-2 paragraphs)

This goes into the MAA's Analysis section. It should:
- Lead with the finding, not the methodology ("The page doesn't match the
  ad's promise", not "We audited the landing page and found...")
- Connect the LP finding to the QS component data ("Below Average LP
  Experience makes sense when you see the disconnect...")
- Be specific about what the gap is, not generic ("The ad promises a free
  maps audit, the page leads with a $1,500/month service qualifier", not
  "There's a mismatch between the ad and the page")
- Acknowledge what the page does well before listing problems. Many of these
  pages were built with care, don't make the page owner feel attacked.

### 2. Action Items (2-3 bullets, max)

These go into the MAA's Action section. Each one should:
- Name a specific change, not a category ("Move the form above the fold",
  not "Improve the page layout")
- Explain why it matters, linked to the analysis ("Right now visitors scroll
  past 1,500 words before they can take action, on mobile that's 4+ screens")
- Note the expected impact on QS or conversion rate where possible
- If the change requires website access the team doesn't have, include the
  offer pattern: "We can help with this if you'd like, we'd just need
  [website access / CMS login / Elementor access]."

**Keep it tight.** The LP audit findings are one component of the MAA, not
the whole document. Two paragraphs in Analysis and 2-3 action items is the
right weight. If the page is mostly fine with one clear problem, one
paragraph and one action item is enough.

## What This Skill Does NOT Do

- Full website audits (SEO, site architecture, information architecture)
- Design critiques (visual aesthetics, brand consistency)
- Competitive landing page comparisons
- A/B test design or statistical analysis of page variants
- Landing page copywriting (the google-ads-copy-optimizer handles ad copy;
  page copy recommendations stay at the directional level)

If the audit reveals that the page needs a significant rewrite or redesign,
say so, but the specific implementation is outside this skill's scope. The
MAA action item should frame it as a recommendation with an offer to help,
not a detailed spec.

## Tone

Write as a partner, not an auditor. The page was probably built by someone
on the client's team or the client themselves. Lead with what works before
noting what doesn't. Frame recommendations as "consider" or "one option
would be" rather than "you need to fix." When recommending changes that
require the client's involvement, address them by name if the narrative
document provides it.
