# Official export and consent guidance

Use the platform's own export. Do not ask for passwords, cookies, tokens, browser automation, or scraping access.

## LinkedIn — recommended first source

On a computer, open LinkedIn **Settings & Privacy → Data privacy → Get a copy of your data**. Request the larger archive that includes connections. LinkedIn may take up to 24 hours and sends the download link to the email already on the account.

Official instructions: https://www.linkedin.com/help/linkedin/answer/a566336/exporting-connections-from-linkedin

The user may provide the untouched ZIP within the safe limits, or extract it locally and supply only `Connections.csv`. Do not request that they email the archive to an operator.

## Google Contacts — fastest alternative

Open Google Contacts, choose the contacts, select **Export**, and choose Google CSV.

Official instructions: https://support.google.com/contacts/answer/7199294

This may contain people saved for many reasons. Label it address-book evidence.

## Facebook

The local CLI does not currently parse Facebook exports. Offer the browser-local Second Ring scan if the user wants its reviewed Facebook adapter, or wait for a versioned local fixture. Never improvise a parser against an unknown JSON tree.

Official export guidance: https://www.facebook.com/help/212802592074644

## Consent test

Before processing, establish one of these:

1. The file is the requester's own export.
2. The owner explicitly supplied it for this analysis.
3. The file is a synthetic fixture.

One person's approval does not grant permission to publish their contacts. Screenshots and case studies need separate, specific permission for every identifiable contact; otherwise use redacted aliases or the built-in demo.
