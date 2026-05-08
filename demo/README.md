# Demo assets

What's in here:

- **`slides.html`** — Self-contained 15-slide deck for demo-day. Open in any browser; arrow keys / space / click to navigate; `f` for fullscreen.
- **`mesh-cinematic-demo.mp4`** — Pre-recorded cinematic walkthrough of the live-narrowing onboarding flow. Use as a fallback if the venue Wi-Fi blocks Weaviate gRPC, or play it before/after the live segment for visual polish.
- **`w1.jpeg` … `w5.jpeg`** — Reference frames / poster images used in the deck or for social.

## Demo-day playbook

1. Open `slides.html` full-screen on the projector.
2. Walk through slides 1–4 (problem → solution → user POV → founder POV).
3. Slide 5 = "live demo" — at this point either:
   - **Path A (live):** switch to `localhost:3000` and walk the user + founder flows in real time.
   - **Path B (recorded):** play `mesh-cinematic-demo.mp4` instead.
4. Resume with slides 6 onward (algorithm, features, learnings).

If the live demo fails mid-stage, falling back to the video is graceful — the slides keep the narrative even if the app doesn't cooperate.
