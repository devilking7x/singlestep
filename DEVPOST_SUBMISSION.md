# SingleStep — One tiny step at a time

**Tagline:** For brains that freeze at long lists: paste the overwhelm, get ONE tiny step.

**Team:** Raza7x (solo)
**Hackathon:** Taskforge — "Work should fit people, not force people to fit the tool."
**Built with:** Python, Flask, Groq (llama-3.3-70b-versatile), HTML, CSS, JavaScript, Tailwind CSS, Web Speech API, Web Audio API

---

## Inspiration / Problem

A 20-item to-do list does not motivate everyone. For people with ADHD, executive
dysfunction, or burnout, a long list triggers task paralysis: the brain sees
everything at once, cannot pick a starting point, and freezes. Traditional
productivity tools show MORE — more lists, more badges, more red overdue
labels — which makes the freeze worse.

SingleStep asks a different question: what if the tool showed LESS, on purpose?
What if it hid the whole queue and showed only one tiny, physical, doable
action — "Open a blank document and type 3 ugly words" — and let the next
step appear only after that one is done?

## Intended User

One person, clearly: someone staring at a pile of work and unable to start.
Our three test personas make it concrete:

- **Maya, ADHD student** — a 12-page paper due tomorrow, 40 unread PDFs, a
  messy desk, panic, and no starting point.
- **Alex, burned-out developer** — a production auth bug blocking release,
  9 PRs waiting, Slack blowing up, and an unwritten post-mortem.
- **Sam, sensory overload at home** — laundry everywhere, dishes piled up, a
  forgotten electricity bill, and packing for a morning train.

If you have ever opened a task app, felt your stomach drop, and closed it
again — SingleStep is for you.

## What it does (Solution)

1. **Brain dump, no structure required.** Type or speak the mess (microphone
   uses the Web Speech API). Messy input is perfect input.
2. **Energy selector.** The user picks their current battery: 10% Survival
   (1–2 minute ultra-baby steps), 50% Steady (5 minute micro-steps), or 90%
   Flow (10–15 minute structured steps). The tool adapts to the human, not
   the other way around.
3. **AI decomposition.** Groq's llama-3.3-70b-versatile turns the dump into
   5–8 concrete micro-steps, each starting with a physical verb, each with
   a duration, an energy tag, and a calm friction-breaker tip.
4. **The Blindfold Arena.** The full list is HIDDEN. Only ONE card is shown:
   the current micro-step, a gentle breathing progress ring, and
   "Step 2 of 8 (7 hidden to protect your focus)". Four single-tap actions:
   Done → Next (with a soft chime and confetti), Still Too Hard → Slice
   Smaller (recursively breaks the step into 3 sixty-second baby steps),
   Swap for an Easier Step, and Read Aloud / hands-free Voice Mode
   ("Done", "Smaller", "Next", "Swap").
5. **Show the difference.** A comparison toggle shows the old way (a
   cluttered list with red badges) next to the SingleStep way (one calm
   card, hidden queue). The cognitive-load figures shown there are
   illustrative estimates, clearly labelled as such.
6. **Accessibility & sensory dock (always visible).** Bionic Reading
   (bolds the first half of each word), dyslexia-friendly typography,
   three sensory themes (Calm Sage, Warm Paper, High-Contrast WCAG AAA),
   and synthesized Brown Noise / Soft Rain soundscapes generated live
   with the Web Audio API — no audio files needed.
7. **Zero friction.** No account, no signup. Everything persists in
   localStorage, with JSON Export/Import. If no Groq API key is present
   (or the API is rate-limited), the app automatically falls back to a
   deterministic heuristic micro-slicer, so it never crashes during judging.

## How we built it (Tools Used)

- **Backend:** Python 3 + Flask (`app.py`), Groq API via plain HTTPS
  (`llama-3.3-70b-versatile`, JSON mode), `python-dotenv`, `flask-cors`.
- **Frontend:** One single-page app (`templates/index.html`) with Tailwind
  CSS (CDN), Lucide icons (CDN), canvas-confetti (CDN), and vanilla
  JavaScript. No build step, no framework.
- **Browser APIs:** Web Speech API (SpeechRecognition + speechSynthesis)
  for voice input, read-aloud, and voice commands; Web Audio API for the
  chime and synthesized soundscapes; localStorage for persistence.
- **Fallback:** A deterministic heuristic slicer in `app.py` (and a
  client-side twin in the frontend) guarantees the demo works even with
  no API key and no network to Groq.

## How to run it (for judges)

```bash
cp .env.example .env   # optional: add GROQ_API_KEY (free at console.groq.com)
pip install -r requirements.txt
python app.py          # open http://127.0.0.1:5000
```

No key? No problem — the app runs fully on the offline fallback.
Click any persona (Maya / Alex / Sam) to see a full demo in one tap.

## Demo video script (60–90 seconds)

1. (0–10s) The problem: show a cluttered 20-item list, red badges — "this
   is what overwhelm looks like."
2. (10–25s) Click **Maya** — her brain dump appears, energy set to Steady,
   click "Slice it into tiny steps".
3. (25–50s) The Arena: ONE card, breathing ring, "Step 1 of 7 (6 hidden)".
   Click "Done — Next" (confetti), then "Still Too Hard — Slice Smaller"
   (one step becomes three 60-second steps).
4. (50–70s) Toggle the comparison view: old way vs SingleStep way.
   Toggle High-Contrast theme + Bionic Reading in the dock.
5. (70–90s) Close: "One tiny step at a time." + streak + export.

## Limitations (honest)

- The cognitive-load percentages in the comparison view (94% vs 14%) are
  **illustrative estimates**, not clinically measured values. They are
  labelled as such in the UI.
- AI decomposition quality depends on the model; the heuristic fallback
  is simpler and less personalized than Groq output.
- Voice features work best in Chrome with microphone permission; every
  action is also available as a button, so voice is never required.
- Soundscapes are synthesized noise, not recorded audio; quality varies
  by device speakers.
- Steps are stored only in the browser (localStorage); there is no cloud
  sync or multi-device support yet.
- Slice-smaller recursion is capped at 2 levels to avoid infinite slicing.

## What we learned

- Showing less is a feature, not a missing feature. Hiding the queue was
  the single most important design decision.
- Judges (and users) need a one-tap demo: personas beat empty input boxes.
- Every AI feature needs an offline fallback, because judging-day
  conditions are never guaranteed.
- Accessibility cannot be a settings page afterthought — it has to be a
  persistent dock, one tap away, always.

## AI Assistance Disclosure

This project was built with AI assistance (Cursor / AI coding tools):
the Flask backend structure, the heuristic fallback, and the frontend
were drafted with AI help and then reviewed, tested, and fixed by the
developer. The product idea, the persona scenarios, the accessibility
requirements, and the final submission text are the developer's own.
All AI-generated code was tested end-to-end (including the no-API-key
fallback path) before submission.

## Submission checklist (for the submitter)

1. Devpost → Taskforge → "Join hackathon" (free).
2. Create project: title **SingleStep**, tagline above, story = this file
   (Problem → Solution → Tools → Limitations → Learned → Disclosure).
3. Add the code: link the public GitHub repo containing this folder
   (or upload a ZIP if the form allows).
4. Add the demo: upload the 60–90 second video (script above) or a
   click-through walkthrough.
5. Team: Raza7x (solo). No pre-existing code is reused except standard
   libraries/CDNs listed above.
6. Submit before **25 Oct 2026, 02:30 AM IST**.
