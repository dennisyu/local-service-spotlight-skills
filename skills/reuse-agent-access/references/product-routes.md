# Product routes and limits

Documentation checked October 14, 2026; this does not certify runtime access.
Product support changes; verify the current app, build, plan and exposed tools
before using a route. “No documented import” means the
reviewed sources do not establish one, not proof that every build lacks it.

| Product / surface | Supported route to investigate | Limit and source |
|---|---|---|
| Claude desktop | Import selected sites' cookies into the built-in browser, or reuse signed-in Chrome through Claude in Chrome. | Import supports Chrome/Edge/Firefox on macOS and Firefox on Windows/Linux beta; not Safari. The built-in browser needs the desktop app open and online, including web/mobile control. [Built-in browser and import](https://support.claude.com/en/articles/16607400-use-the-built-in-browser-in-claude-cowork) |
| Codex / ChatGPT desktop app with browser extension tools | Use the supported extension in the intended Chrome, Edge, Brave, Opera or Vivaldi profile; verify a site read. | Availability depends on build and workspace. `@Browser` uses a separate built-in browser. [Browser extension](https://learn.chatgpt.com/docs/chrome-extension) |
| ChatGPT cloud browser | Use its secure sign-in form and retained browser session. | Its browser is separate from the device browser and does not use the device's cookies. [Cloud browser](https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt) |
| ChatGPT Atlas | Retired; do not recommend for new setup. | Existing browser data does not automatically transfer to a supported browser. [Atlas retirement](https://help.openai.com/en/articles/20001371-chatgpt-atlas-retirement) |
| Cursor | Native browser keeps workspace session state. A compatible local browser bridge can reuse Chrome when installed and enabled. | Native persistence is isolated per workspace; the native browser docs do not establish Chrome import. Kimi lists Cursor as a supported local agent for its extension. [Cursor browser](https://prod.cursor.com/docs/agent/tools/browser), [Kimi setup](https://www.kimi.com/en/help/kimi-webbridge/kimi-webbridge-introduction) |
| Kimi Work | Select an existing connected service plugin with `/`. Use the supported browser extension if needed; on Mac, Work also documents Chrome-cookie import into its built-in browser. | Import was introduced in Work 3.2.0 and is off by default; inspect current Settings and consent. This Work-only import route is not a Code or web-chat claim. [Work plugins](https://www.kimi.com/en/help/kimi-work/plugin-center), [Work release notes](https://www.kimi.com/en/help/kimi-work/release-notes) |
| Kimi Code / Kimi browser sidebar | Kimi Browser Extension, formerly WebBridge, uses the real Chrome/Edge browser and its signed-in sessions. | Code needs its companion plugin or skill plus the browser extension. Plain web chat is a different surface. Local-agent mode does not require Kimi account sign-in. [Kimi plugins](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins), [official extension](https://chromewebstore.google.com/detail/kimi/fldmhceldgbpfpkbgopacenieobmligc) |
| Qwen Code | Browser Use reuses Chrome sessions through its official extension. | macOS/Linux, Chrome 125+, Qwen Code 0.24.2+. Use the Chrome Web Store route; source build is a regional fallback. Keep one extension copy per profile. This does not establish Qwen web-chat access or installation. [Browser Use](https://qwenlm.github.io/qwen-code-docs/en/users/features/browser-use/) |
| Qwen or another model inside a host app | Inspect the host's actual browser/connector tools. | Model weights and a local inference worker do not themselves contain Chrome access. Use the host's verified route; do not create a second runtime merely because its name matches the model. |
| Grok web | Existing OAuth connectors; custom remote MCP where supported and authorized. | No Chrome password/cookie import is established by these docs. A public MCP endpoint requirement is not permission to expose a desktop browser bridge. [Grok connectors](https://docs.x.ai/grok/connectors) |
| Grok Bot | Inspect the selected computer. Cloud browser sessions persist and are shared across the user's Bots; local execution is separately enabled. | Official documentation now covers local Mac/Windows execution. That does not establish Chrome profile reuse; verify a site read. [Computer and apps](https://docs.x.ai/grok-bot/computer-and-apps), [mobile](https://docs.x.ai/grok-bot/mobile) |
| Muse | Reuse connected services and persistent browser access; use its secure credential UI when sign-in is required. Inspect Mac local-app/tab tools where available. | Meta describes a persistent secure VM and credentials held outside the model. Mac app access does not establish Chrome import; the product page lists 1Password integration as coming soon at review time. [Muse security design](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse), [Muse capabilities](https://ai.meta.com/muse/) |

An agent's ability to reuse a session is distinct from its ability to read a saved
password. Native import, an authenticated connector, browser session persistence
and remote control are different mechanisms. No verified route promises that all
saved passwords or every site's session works across all these products.

## Kimi Work: a connected plugin has no tools in the task

Try one fresh Work task and choose the existing plugin from the `/` menu. Ask the
agent to load the offered connector tool when the runtime provides a tool loader,
then run one harmless account read and inspect its actual result. Loading a tool
does not complete the read. This recovery check does not guarantee that every
connected plugin is available in a fresh task. If it remains unavailable, use the
next supported route before requesting new authorization.

## Cross-agent local browser bridge

Kimi's [official setup guide](https://www.kimi.com/en/help/kimi-webbridge/kimi-webbridge-introduction)
names Codex, Cursor, Claude Code, Kimi Code and other local agents. Prefer an
already working native bridge. When installing Kimi's bridge is needed and within
scope, use the official extension plus the appropriate desktop plugin or CLI
setup, inspect changes before applying them, and preserve existing skill edits.
The desktop and standalone daemon installers have different responsibilities.

Check the installed bridge's status and documented local address. Extension
connected means transport is ready; verify the target site and intended account
next. Local execution keeps session storage in the browser, but requested page
results may enter the agent's model context. Do not promise that all page content
remains on-device merely because the bridge is local.

## Instruction discovery and distribution

Use the installed version's documented paths; these are instructions, not places
to store credentials. Preserve existing files and merge narrow instructions rather
than replacing a user's entire configuration.

| Runtime | Documented route |
|---|---|
| Cursor local | `~/.agents/skills/<name>/SKILL.md` or `~/.cursor/skills/<name>/SKILL.md`; compatible Codex/Claude skill folders also work. Only `~/.cursor/skills/` supports the documented personal Cloud Agent sync control. Instruction sync does not establish browser sign-in transfer. [Cursor skills](https://prod.cursor.com/docs/skills) |
| Kimi Code | `~/.agents/skills/` or `~/.kimi-code/skills/`; current global instructions can use `~/.agents/AGENTS.md` or `~/.kimi-code/AGENTS.md`. Older installs may use `~/.kimi`; inspect the version. [Kimi skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html), [Kimi instructions](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents) |
| Qwen Code | `~/.qwen/skills/<name>/SKILL.md`, global `~/.qwen/QWEN.md`, or project `AGENTS.md`. [Qwen skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Qwen memory](https://qwenlm.github.io/qwen-code-docs/en/users/features/memory/) |
| Other local apps or cloud agents | Inspect their supported skill, project-file, memory or instruction UI. Attach/import the public procedure where supported and prove fresh-session discovery; do not invent a filesystem path or assume a URL gets loaded automatically. |

### Activate in Muse, Grok, Grok Bot or a web-only runtime

Open the supported skill, project-file or instruction settings. Add the procedure
there when the app permits it; otherwise use it in the task itself. Refresh an
existing installed copy through that app's update/import control while preserving
custom edits. Start a new task and confirm which revision is loaded. A chat memory
or link in one task is not proof of future discovery.

Copy this prompt after the skill is published to the canonical repository:

> Read https://github.com/dennisyu/local-service-spotlight-skills/blob/main/skills/reuse-agent-access/SKILL.md
> and its linked product reference. Apply it to the site and task I name here,
> using only access already authorized for that task. Identify your actual app
> and execution environment. Check an existing connector or supported signed-in
> browser before requesting another login. Perform one harmless read in the
> intended account. Report the source revision, whether the skill loaded, the
> selected route, non-secret account check, result and last-verified time. Keep
> credentials and the personal access inventory private. If the source cannot be
> loaded or consent/login is missing, report that exact gap. Save the instructions
> in this app's supported reusable location if available, then tell me how a new
> task can verify discovery. Do not claim this has installed or enabled access
> in other apps.

Replace “the site and task I name here” with the actual service and permitted
read. If the runtime cannot read GitHub, attach the reviewed skill and reference
files through its supported UI. A fresh task that loads them and verifies the
read is the acceptance check; an import toast or a model repeating this prompt
is insufficient. Retain the installed/source revision in the private receipt.

## iPhone and iPad

A desktop Chrome extension route is not an iOS installation recipe. A phone may
control a supported remote agent whose desktop or cloud session is already signed
in; verify which machine actually runs the tools. Use that product's supported
mobile/cloud connector or secure login flow when needed. Do not claim that Chrome
sync, a password-manager app, or this skill automatically transfers another app's
cookies on iOS. Keep platform consent and device-unlock steps with the user.
