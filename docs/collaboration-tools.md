# Collaboration Tools (proposal, decision B11)

Principle: one-day event, so as few tools as possible. Every extra tool costs setup time and splits information. The documentation deliverable is technical, so it belongs next to the code.

## Recommended minimum set

| Need | Proposal | Why | Alternative |
|---|---|---|---|
| Chat | The channel the event already uses (often Discord), else a WhatsApp/Signal group | Zero setup | Slack (overkill for one day) |
| Code + docs | **One GitHub repo**: code, Markdown docs (this `shared/` folder becomes `docs/`) | Docs live with code; the documentation deliverable is ready at submission; one link for the jury | GitLab |
| Backlog + kanban | **GitHub Projects** board in the same repo (see below) | Free; cards link to issues, PRs and commits; no second tool | Notion board, Trello |
| Diagrams | **Mermaid** in Markdown (renders on GitHub) for state machine and sequence; **Excalidraw** for quick whiteboard sketches | Mermaid stays versioned; Excalidraw needs no account and supports live collaboration | draw.io, tldraw |
| Pitch slides | AI draft (Claude / ChatGPT → `.pptx`, or Gamma) → import into **Google Slides** for team edits | AI makes the first draft from `templates/pitch-outline.md` + docs; Google Slides for live co-editing and presenting. Declare the AI tool in the declaration log | Gemini in Slides (paid plans), Canva |
| API testing | **Bruno** (collections are plain files in the repo) or curl scripts | Shared request collection without accounts | Postman (needs workspace and login) |
| Secrets | `.env` per laptop, never committed. Share credentials in person or via a password manager share | Ecurious credentials must not leak (Fair Play) | – |
| Demo fallback video | QuickTime / OBS / phone | Already installed | – |

## Task board (backlog + kanban)

GitHub Projects, Board view. Seed from `backlog.md`. Free, also on a personal account: create it under the repo owner's profile (Projects tab → New project), link it to the repo, and add teammates as collaborators of the repo and the project. No organisation needed.

| Column | Meaning |
|---|---|
| Backlog | Known, not planned yet |
| Todo | Next up, for the current gate |
| In progress | Max 1 card per person |
| Review | Needs a second person (code review, demo check) |
| Done | Merged or verified |

Custom fields (keep few):

- **Gate**: Prep, G0, G1, G2, G3, G4 – filter by current gate
- **Priority**: P0–P3 (see `hackathon-playbook.md` §7)
- **Area**: Core, No-Shows, Blocked, Plate, Interop, Business, Docs, Pitch
- **Owner**: GitHub assignee

Rules: cards ≤ 1 hour of work, else split. Draft items for quick notes; convert to issue when code is involved. A card that failed goes to Done with label `did-not-work` – feeds the documentation section.

If the team prefers Notion: use a Notion board for tasks only, keep docs in the repo. Never both boards.

## Where Notion fits

| Use Notion if… | Skip Notion if… |
|---|---|
| Teammates are non-developers and dislike Markdown/GitHub | Everyone can use GitHub |
| You want a nicer prep space before the event (meeting notes, idea board) | Docs would be written twice (Notion + repo) |

Middle way: Notion (or Google Docs) only **before** the event for discussion; on event day everything moves into the repo. Do not run both on the day.

## Before the event

- [ ] Agree chat channel
- [ ] Create GitHub repo, add everyone, push `shared/` as `docs/`
- [ ] Check everyone has: GitHub account, git, editor, Node/Python (per B1), Bruno or curl
- [ ] Create Google Slides from `templates/pitch-outline.md`

## Data rules for all tools

- No real license plates or photos of real cars in chat, slides or repo, unless people consented. Use test plates.
- No credentials in screenshots or slides.
