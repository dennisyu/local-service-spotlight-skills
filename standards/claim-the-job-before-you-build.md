---
{
  "title": "Claim the job before you build",
  "severity": "error",
  "captured": "2026-09-29",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-29: 'What do we need to do with our shared training or the way we talk to our agents so I can literally have a conversation with one agent, then move it seamlessly to another agent? I can operate without having to remember which agent I last talked to about a particular project, and I can have QA loops at many levels.' Captured the morning three agents on three models each built and delivered the same partner guide inside two hours, and a fourth job mailed the same partner, because no agent had written 'I have this' where the others look.",
  "source": "https://dennisyu.com/agent-disclosure/",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Claim the job before you build

- **Before you build anything that will outlive this session, reach outside
  your own repository, or be seen by anyone but the person who asked, write
  "I have this" where every other agent looks — and look there first.** A claim
  is a line in a shared file with your name, the ask in the human's own words,
  and the state of the work; it is not a feeling, a chat message, or a plan to
  write a note afterwards.
- **Why:** on 29 September 2026 one founder asked for one partner guide. Three
  agents on three models each built one and each delivered one inside two hours
  — 31, 24 and 41 pages, three signatures, three descriptions of the same fleet
  — and a fourth job mailed the same partner the same morning. Every agent
  followed every rule it could see. None could see each other, because the
  first move was a sentence in a file nobody was required to act on. The
  partner received four messages; the founder received a mess to explain. The
  build cost was three agents' mornings; the trust cost was higher.
- **How, in order:** (1) *Find* — search the shared job folder, both status
  boards, the newest notes, and the sent mailbox for the recipient and the
  topic. A live match means you pick it up and continue from its last
  checkpoint and next click; never a second copy. (2) *Claim* — if nothing
  matches, open one job packet: the ask verbatim, your name as owner, the desk
  that owns the outcome, the class of work, who it will be delivered to, and a
  date on which someone must come back. (3) *Checkpoint* every human-visible
  action in that packet, with something a stranger can open. (4) *QA by rung*:
  nothing leaves the house before a second look by a context that did not write
  it; a partner, client, public, or shared-rule deliverable is not done until a
  *different model* has read it and recorded the result. (5) *Close* with a
  Verified line. In the agent runtime this is `tools/job_packet.py` (`find`,
  `new`, `claim`, `checkpoint`, `qa`, `close`); anywhere else it is the same
  five moves in whatever shared file the team reads first.
- **The same ask given to several agents on purpose is a bake-off.** Every
  entry is marked as one, every deliverable goes to the requester, and nothing
  reaches the outside party until the requester picks. If you find a live claim
  on your ask and were not told "bake-off", assume it is one: build if you
  must, deliver to the requester, never to the partner. Delivery to the outside
  party is the irreversible step; that is where the gate sits.
- **One lane per partner per day.** Before any message, file, or share leaves
  for a client, partner, or the public, check whether anyone on the team
  already reached that party today. If so, bundle or hold; do not add a second
  lane. Four touches in an hour from one company reads as four companies.
- **Hand off instead of stopping.** When your session ends, when a different
  runtime can do the next step, or when the human says "move this", write the
  state of play and the single next click into the packet and name the next
  owner. The human should be able to say "pick up X" to *any* agent and have
  it continue — they never have to remember which agent they spoke to last.
- **What does not need a packet:** a one-command internal fix, a routine reply
  the team has already authorized, a daily sweep. When in doubt, the search
  costs three seconds; the collision costs a partner.
- **Exemption:** none for external deliverables. An internal job may skip the
  packet only when it is reversible, finishes in the same session, and no one
  else will read its output; write `no packet: <reason>` in your note so the
  choice is visible.
