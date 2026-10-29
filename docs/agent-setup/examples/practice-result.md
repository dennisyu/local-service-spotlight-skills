# practice-001 — source updates and tested installations

A source update makes revised instructions available for adoption. A tested installation needs evidence from the named product, account and runtime after that runtime has received the revision. This is local practice for learning that distinction.

| State | Evidence required | What source editing alone establishes |
|---|---|---|
| Available | The exact revision is readable in its maintained repository or release. After merge, a source change can establish this state there. | Availability of those bytes at that source, not an account update. An unmerged candidate is only candidate source. |
| Installed | The named runtime/account has installed or updated the intended package/revision through its supported route. Record the displayed version or revision. | No installed-account evidence. Copying starter workspace files does not install a skill. |
| Enabled | The named runtime/account has enabled the selected installed skill or bundle. Keep actual surface evidence. | No enabled-account evidence. A repository manifest's list is not the account's enabled list. |
| Tested | In a fresh chat/session, the selected skill actually loads, produces a result, and that result is checked against its acceptance criteria. Record the exact source/installed revision and observed result. | No tested-runtime evidence. Source validators and this written explanation do not show runtime activation. |

For a source update, acceptance sections B and F separate source synchronization from account adoption: sync/update the named account, inspect its new revision/canary, then run a fresh activation and behavior test. An observed manual update verifies that update route; claiming automatic updates requires observing an unattended update on that account. Section A requires all its fresh-account install steps before that install test passes. See [ACCEPTANCE.md, sections A, B and F](source-snapshot/ACCEPTANCE.md).

The other states also have separate evidence: Delivered requires the intended receiver to open and acknowledge this exact artifact revision; Scheduled requires a job definition; Observed requires a real firing with a timestamped output or failure. This one-off exercise needs no schedule. Review independence and exact-revision continuation are covered in [ACCEPTANCE.md, sections D and H](source-snapshot/ACCEPTANCE.md).

What happened here: the worker read candidate public instructions, copied the starter into an authorized local folder, recorded one task claim and wrote this result. This proves local file-capable practice for this worker. The candidate instructions are pinned in source-manifest.json and source-snapshot/ over base commit 0095d089d8fa9a27177b4aae35dcb5c110e1da0e; they are not asserted to be released at that commit.

This exercise does not prove any skill was Installed, Enabled or Tested in an account, that another agent received this result, that any scheduled job ran, or that client/business results improved. The producer's save receipt is not delivery. A later fresh-context agent in the same harness can test record portability; that would still not prove a separate product session, another model's agreement or all-model consensus.
