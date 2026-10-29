# Coordination Starter — run multiple AI agents off one shared repo

By Dennis Yu / Local Service Spotlight. This is the starter copy of the system
described in [How the Agents Run the Company](https://dennisyu.com/how-agents-run-the-company/).

## The idea in one paragraph

Your agents (ChatGPT, Codex, Claude, Grok, Muse, Cursor — any mix) do not
share a brain. They share files. One private GitHub repository is the shared
job board and memory: every task is claimed before it is worked, every result
is linked from the board, and every handoff is written down where the next
agent can read it. Chat is where agents talk. The repo is what they agreed.

## Set it up (15 minutes)

1. Create a **private** GitHub repository, e.g. `agent-coordination`.
   Never put passwords, API keys, or client records in it.
2. Copy these files from this folder into the repo root:
   - `AGENTS.md` — the rules every agent reads first
   - `JOBS.md` — the job board (one row per task)
   - `NOW.md` — what is active right now, who owns it
   - `SHARED-MEMORY.md` — facts every agent should know, dated
   - `decisions/DECISIONS.md` — decisions the human made, verbatim, so agents
     never have to ask the human to re-approve agent-to-agent steps
3. Connect each agent to the repo the way that tool supports: a GitHub
   connector, a plugin/marketplace install, a local clone, or a scheduled
   pickup. A repo alone does not wake an agent — each agent needs a route in
   and a time to check. Test the route with one harmless read before you
   trust it with real work.
4. Run **one real task between two agents** end to end (claim → work →
   receipt → handoff) before adding the rest of your fleet.

## The loop every agent follows

1. **Read** `NOW.md` and `JOBS.md` before starting work.
2. **Claim** the task: put your name and the time on its row. A fresh claim
   means nobody else starts the same work.
3. **Work** inside the claim. Keep notes in the task's own file, not in chat.
4. **Verify** the result where it landed (the live page, the sent thread,
   the booked record) — not from your own draft.
5. **Receipt**: mark the job done with a link to the result and the check
   you ran. A claim of done without a link is not done.
6. **Hand off** in writing: what is finished, what is not, what the next
   agent should do first. Also post a short pointer in the channel the next
   agent actually watches — a filing nobody sees is not a handoff.

## Rules that keep it from falling apart

- **One owner per job.** Two owners means no owner.
- **Silence is not agreement.** A handoff is real when the receiver
  acknowledges it in the record.
- **The human is not the messenger.** Decisions the human makes get filed
  in `decisions/DECISIONS.md` the same day, verbatim. Agents cite the
  decision instead of asking the human again.
- **Absence needs two checks.** Before anyone reports "missing / not sent /
  not posted", check twice, at least once at the destination itself.
- **Lessons become rules.** When a run teaches something, update the skill
  or this file in the same session — then every agent has it next run.

## Going further

- The full method, with worked examples and QA ladders:
  https://dennisyu.com/how-agents-run-the-company/
- The skill library our agents run (installable, free):
  https://github.com/dennisyu/local-service-spotlight-skills
- How a rule learned on one desk reaches every agent:
  https://dennisyu.com/how-skills-propagate/

Last updated: 2026-10-29 · Edition: starter v1.0
