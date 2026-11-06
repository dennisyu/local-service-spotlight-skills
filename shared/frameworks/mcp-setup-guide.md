# Google Ads MCP Setup Guide

How to connect the analyzer's primary data source: the official **Google Ads
MCP server** (`googleads/google-ads-mcp`). Once connected, the analyzer pulls
every MAA dataset live via GAQL (`gaql-query-pack.md`), correctly-labeled data,
no email plumbing, and mid-analysis follow-up pulls.

**What you get:** a read-only bridge to the Google Ads API with three tools:

- `list_accessible_customers`, the customer IDs and account names the
  authenticated user can reach
- `search`, executes GAQL queries (this is what the analyzer uses)
- `get_resource_metadata`, field/structure reference for a resource type

**Read-only is enforced by the server itself** (current release). It cannot
modify bids, pause campaigns, or create assets, which is exactly the boundary
this skill set wants. Account changes go through `google-ads-change-scripts`.

Official reference: Google's developer integration guide at
developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server and the
github.com/googleads/google-ads-mcp repository.

---

## Before you start (one-time, per organization)

You need three credentials before configuring anything. For a first-timer this
is the longest part of setup, budget an hour of clicking plus up to a few
business days of waiting on Google's access approval. Work through these in
order:

### 1. Developer token (from your Google Ads MCC)

Where it lives: sign in to your **MCC** (manager account) → **Tools** →
**Setup** → **API Center**. The token is a 22-character string.

⚠️ **Test access vs Basic access, the most common first-run failure.** A new
token starts with **test access**, which can ONLY query test accounts. Queries
against live client accounts fail with an authorization error that does not
obviously say "your token is test-level." To reach live accounts you must apply
for **Basic access** from the same API Center page: the form asks about your
company, the tool you're building (an internal reporting integration is fine),
and API usage. Approval is manual and typically takes 1–3 business days,
apply on day one, before doing anything else, so the wait overlaps the rest of
setup.

### 2. Google Cloud project with the Google Ads API enabled

Any GCP project you control. Enable the API with:

```
gcloud services enable googleads.googleapis.com --project YOUR_PROJECT_ID
```

or in the console: APIs & Services → Library → search "Google Ads API" →
Enable.

### 3. OAuth client (from that GCP project)

Console → APIs & Services → Credentials → Create credentials → OAuth client ID.
The application type depends on how you'll run the server:

- **Desktop app**, for Option 1 (local stdio). No redirect URI needed; the
  first run opens a browser consent flow.
- **Web application**, for Option 2 (Cloud Run). You'll add the Cloud Run
  URL's OAuth callback as an authorized redirect URI after the first deploy
  (see Option 2's two-pass note).

**Publish the OAuth consent screen to Production before going live** (Console →
APIs & Services → OAuth consent screen → Publish app). An app left in
"Testing" status issues refresh tokens that **expire after 7 days**, which
presents later as the connection demanding reauthorization every few days.
Doing this now prevents the problem; doing it later means re-authorizing one
more time after you flip it. (This is the root cause behind the
reauthorization limitation at the bottom of this guide.)

The Google account you authorize with must have access to the accounts you'll
query, for an agency, that means a user on the MCC.

**Agency/MCC note:** authorize with a user on the MCC and every client account
under it becomes reachable. The analyzer passes the child account's CID as
`customer_id` on each query, record each client's CID (digits only, no dashes)
in your per-client notes so runs don't start with a lookup.

---

## Option 1, Run it locally (stdio)

Best for a single operator on one machine. Add this to your MCP host's config
(Claude Code: `.mcp.json` in the project or `~/.claude.json`; other hosts:
consult their docs):

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "command": "pipx",
      "args": [
        "run",
        "--spec",
        "git+https://github.com/googleads/google-ads-mcp.git",
        "google-ads-mcp"
      ],
      "env": {
        "GOOGLE_PROJECT_ID": "YOUR_PROJECT_ID",
        "GOOGLE_ADS_DEVELOPER_TOKEN": "YOUR_DEVELOPER_TOKEN"
      }
    }
  }
}
```

Requires `pipx` installed. On first run it walks you through the OAuth consent
flow in a browser.

## Option 2, Deploy to Cloud Run (shared / remote)

Best when several people or a Cowork/desktop environment need the same server,
or you want it reachable as a URL connector.

⚠️ **This is a two-pass deploy.** `GOOGLE_ADS_MCP_BASE_URL` must be set to the
service's own URL, but Cloud Run only assigns that URL after the first deploy.
So: deploy once without it, read the URL back, then update the service with the
variable set (and add the URL's OAuth callback to your Web OAuth client's
authorized redirect URIs). Skipping the second pass is the classic
lost-hour here, OAuth appears to start and then fails on redirect.

Concrete sequence (substitute your project, region, and values):

```
# one-time: build infra
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
gcloud artifacts repositories create google-ads-mcp \
  --repository-format=docker --location=us-central1

# build the image from the google-ads-mcp source checkout
git clone https://github.com/googleads/google-ads-mcp.git && cd google-ads-mcp
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/google-ads-mcp/server

# PASS 1, deploy without the base URL
gcloud run deploy google-ads-mcp \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/google-ads-mcp/server \
  --region us-central1 \
  --set-env-vars GOOGLE_PROJECT_ID=YOUR_PROJECT_ID,\
GOOGLE_ADS_DEVELOPER_TOKEN=YOUR_DEV_TOKEN,\
GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=YOUR_CLIENT_ID,\
GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET,\
FASTMCP_HOST=0.0.0.0

# read the assigned URL back
gcloud run services describe google-ads-mcp --region us-central1 \
  --format='value(status.url)'

# PASS 2, update with the base URL set to that value
gcloud run services update google-ads-mcp --region us-central1 \
  --update-env-vars GOOGLE_ADS_MCP_BASE_URL=https://YOUR-ASSIGNED-URL.a.run.app
```

Then add `https://YOUR-ASSIGNED-URL.a.run.app/oauth/callback` (or the callback
path your server version documents) to the Web OAuth client's authorized
redirect URIs, and point your MCP client at the deployed URL:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "httpUrl": "https://your-cloud-run-url.a.run.app/mcp"
    }
  }
}
```

In Claude Cowork / desktop, add it as a custom connector with that URL and
complete the OAuth flow when prompted.

---

## Verify the connection (5 minutes)

1. Ask: *"What customers do I have access to?"*, should return your account
   list via `list_accessible_customers`.
2. Record each client's CID from that list into your per-client config.
3. Ask: *"Pull the 7-day campaign summary for {client} via the Google Ads MCP"*
the analyzer runs the campaign query from `gaql-query-pack.md`. Spot-check
   the numbers against the Google Ads UI. Remember cost comes back in micros
   (divide by 1,000,000) and rates as 0–1 fractions.

If a field name errors, use `get_resource_metadata` for that resource instead
of guessing.

---

## Known limitation: reauthorization

Depending on your OAuth app's publishing status and token handling, the
connection may require frequent, even daily, reauthorization. In practice
this is the main blocker to fully hands-off scheduled runs: if the `search`
tool is missing when a run starts, the authorization has lapsed.

Mitigations, in order of preference:

1. **Publish the OAuth app to production** (an app left in "Testing" status
   issues refresh tokens that expire after 7 days) and verify refresh-token
   persistence in your deployment.
2. **Keep the email pipeline wired as the fallback** (`WALKTHROUGH.md`, Path B)
   so a scheduled run degrades to the email data instead of stalling.
3. **Reauthorize before scheduled runs** if neither of the above is in place
   yet.

---

## What the analyzer expects once connected

- Queries per `gaql-query-pack.md`: campaign summary, keyword report + QS
  components, search terms, ad report, conversion detail, each in 7D and 30D
  windows.
- **QS components read AS-IS** on this path. The column swap in the
  data-pipeline contract is for the email fallback only.
- LSA campaigns will appear in pulls (`advertising_channel_type =
  LOCAL_SERVICES`); they are out of scope for the MAA, omit them.
- The MCP is never used to change the account. Changes ship as dry-run-first
  scripts via `google-ads-change-scripts`.
