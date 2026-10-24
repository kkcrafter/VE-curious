# Submission Deliverables

What goes into the organiser's submission form, and what must be deployed so the jury can open it. Deadline 18:00; finish ≥ 30 min before (`hackathon-playbook.md` §3).

The jury opens the links after the event, on their own devices. Nothing on our laptops is running then. A `localhost` link is worth nothing.

## Form fields → our deliverables

| Form field | What we submit | Priority |
|---|---|---|
| Link to Your Prototype / Demo | Demo video link (YouTube unlisted or Loom). Put repo + live URL in the video description | 1 |
| Final Pitch Presentation (PDF) and Prototype | Pitch PDF (`templates/pitch-outline.md`). Optional: Android APK if we build a mobile app | 2 |
| Link to Additional Files (Optional) | Public GitHub repo, or a Drive folder with repo link, screenshots, event log excerpt | 3 |
| Submission Confirmation | Tick | – |

## Ranked deliverables

1. **Demo video, 2–3 min.** S1 full cycle on real hardware + one edge case. Strongest proof: the hardware will not be there when the jury looks again. Record as soon as S1 works, re-record later if time allows.
2. **Public app URL, mock mode on.** Deployed app with the mock adapter (playbook §1, level 2), labelled "simulated hardware". Seeded data: no sign-up, no empty screen.
3. **Public GitHub repo.** README: what it does, screenshot, video link, live URL, how to run, architecture link. Builds from a clean clone; `.env.example` complete; no secrets.
4. **Pitch PDF.**

## Deployment (minimum)

Depends on stack choice (`prep-plan.md` B1). Lazy defaults:

| Piece | Option |
|---|---|
| Web frontend | Vercel or Netlify. Free, deploys on `git push`, preview URL per branch (enough for team collaboration, no private dev server needed) |
| Backend API | Serverless functions in the same Vercel project, or Render / Railway if long-running |
| Database / auth | Supabase or Firebase, only if needed |
| Mobile app | No store release (review takes days). Expo: share QR via EAS Update, or web build on the same URL. Otherwise APK upload, or show it only in the video |
| Webhooks from Ecurious | Needs a public URL (`prep-plan.md` C9). The deployed backend covers it; a tunnel (e.g. ngrok) works for the day only |

Rules:
- Secrets only as env vars on the host, never in the repo or client code.
- Public deployment runs **mock mode only**. No Ecurious credentials on a link the whole world can open.
- If the app calls a paid API (LLM, maps), set a spending cap or rate limit.
- Open the public URL once from a phone on mobile data before submitting.
