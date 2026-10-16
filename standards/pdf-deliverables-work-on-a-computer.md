---
{
  "title": "PDF deliverables work on a computer as well as a phone",
  "severity": "error",
  "captured": "2026-10-16",
  "captured_from": "Dennis Yu, claude.ai session (personal-brand audit), 2026-10-16 20:35 SGT: 'in our PDF audits, if they open on a computer, let's make it easy for them to implement. My guess is the QR code is for when they open on a phone.' (typed text de-doubled)",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## PDF deliverables work on a computer as well as a phone

- **Every QR code in a PDF deliverable gets a one-click twin.** A QR serves the reader
  holding the PDF on paper or on another screen. Many readers open the PDF on the computer
  they would act from, and a QR on that same screen is a dead end.
- Beside every QR, ship both:
  1. a large clickable button that names the action and shows the destination, for
     example "Install the agents → localservicespotlight.com/install/". The link target
     is the full `https://` URL the QR encodes;
  2. the QR image itself wrapped in a link to the same URL.
- **Beside an install or implementation QR, also ship a copy-paste starter prompt** as
  selectable text, not an image: what to paste into a new AI task with the PDF attached.
  Name the deliverable's first-week action IDs and keep every human gate, for example:
  "Use the Local Service Spotlight skills (lss-everything). Read the attached audit and run
  the first-week actions on page 18 (<IDs>) one at a time: draft each change, list the
  access you need (never ask for a password in chat), and wait for my approval before
  anything is published, sent or paid for. Log each step by action ID." Keep it under
  about 60 words.
- **Why:** a QR cannot be scanned from the screen it is displayed on. A reader at a
  computer needs a link to click and words to paste, or the first step stalls.
- **Acceptance:** in the rendered PDF, the button and the QR image each carry a link
  annotation to the same URL the QR decodes to; the starter prompt extracts as text
  (PyMuPDF `page.get_text()`), not only as pixels; and every action ID the prompt names
  exists in that same PDF's action plan.
- **Exemption:** a print-only piece with no digital copy, such as a stage handout,
  needs only the QR and the printed full URL. Say so in the receipt.
