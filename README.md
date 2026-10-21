# SingleStep — One tiny step at a time

For brains that freeze at long lists: paste the overwhelm, get **ONE tiny step**.

SingleStep is an accessible, neuro-inclusive "Zero-List" anti-overwhelm task
engine built for the **Taskforge** hackathon ("Work should fit people — not
force people to fit the tool"). Instead of showing a 20-item to-do list, it
converts a messy brain dump into micro-steps and hides the queue — showing
only one tiny actionable card at a time.

**Team:** Raza7x (solo) · **License:** MIT

## What it does

- **Brain dump, no structure required** — type or speak (microphone uses the
  Web Speech API). Messy input is perfect input.
- **Energy selector** — 10% Survival (1–2 min ultra-baby steps), 50% Steady
  (5 min micro-steps), 90% Flow (10–15 min structured steps).
- **AI decomposition** — Groq `llama-3.3-70b-versatile` turns the dump into
  5–8 concrete micro-steps, each starting with a physical verb.
- **Blindfold Arena** — only ONE card is shown, with a breathing progress
  ring and "Step 2 of 8 (7 hidden to protect your focus)". Actions:
  Done → Next, Still Too Hard → Slice Smaller (3 sixty-second baby steps),
  Swap for an Easier Step, Read Aloud / hands-free Voice Mode.
- **Compare view** — Traditional cluttered list vs SingleStep calm view.
  (Cognitive-load figures shown there are illustrative estimates.)
- **Accessibility dock** — Bionic Reading, dyslexia-friendly typography,
  three sensory themes (Calm Sage, Warm Paper, High-Contrast WCAG AAA),
  synthesized Brown Noise / Soft Rain (Web Audio API, no audio files).
- **Zero friction** — no account, no signup. Data lives in localStorage,
  with JSON Export/Import.

## One-tap judge demos

Click a persona — no typing needed:

- 🎓 **Maya (ADHD Student)** — 12-page paper due tomorrow, 40 unread PDFs.
- 💻 **Alex (Burned-Out Dev)** — production auth bug, 9 PRs, unwritten post-mortem.
- 🏠 **Sam (Sensory Overload)** — laundry, dishes, a forgotten bill, packing for a train.

## Run it

```bash
cp .env.example .env   # optional: add GROQ_API_KEY (free at console.groq.com)
pip install -r requirements.txt
python app.py          # open http://127.0.0.1:5000
```

**No key? No problem.** Without a Groq key (or if the API is rate-limited),
the app automatically uses a deterministic heuristic micro-slicer, so it
never crashes during judging.

## Files

- `app.py` — Flask backend: `GET /`, `POST /api/decompose`, `POST /api/slice-smaller`
- `templates/index.html` — the full single-page frontend
- `requirements.txt`, `.env.example` — setup
- `DEVPOST_SUBMISSION.md` — the complete Devpost write-up (problem, user,
  solution, tools, limitations, what we learned, AI disclosure)
