"""SingleStep — accessible, neuro-inclusive "Zero-List" anti-overwhelm task engine.

Backend: Flask + Groq (llama-3.3-70b-versatile) with a bulletproof deterministic
heuristic fallback. If GROQ_API_KEY is missing, invalid, rate-limited, or the
model returns unusable JSON, the app automatically falls back to the heuristic
micro-slicer so the demo NEVER crashes during judging.

Endpoints:
  GET  /                  -> renders templates/index.html
  POST /api/decompose     -> {brain_dump, energy_level, persona} -> micro-steps
  POST /api/slice-smaller -> {step_title, context} -> 3 ultra-tiny substeps

Run:
  cp .env.example .env   # optional: add GROQ_API_KEY (free at console.groq.com)
  pip install -r requirements.txt
  python app.py          # serves on http://127.0.0.1:5000
"""

import json
import os
import re

import requests
from flask import Flask, jsonify, render_template, request

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from flask_cors import CORS
    _HAS_CORS = True
except Exception:
    _HAS_CORS = False

app = Flask(__name__)
if _HAS_CORS:
    CORS(app)
else:
    @app.after_request
    def _add_cors_headers(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# Deterministic heuristic micro-slicer (offline fallback)
# ---------------------------------------------------------------------------

_PHYSICAL_VERBS = {
    "open", "grab", "write", "read", "put", "pick", "move", "wash", "fold",
    "pack", "call", "send", "type", "list", "sort", "clear", "wipe", "set",
    "start", "take", "check", "draft", "save", "close", "stand", "sit",
    "drink", "breathe", "plug", "charge", "search", "create", "make", "pay",
}

_VERB_BY_KEYWORD = [
    (("paper", "essay", "write", "draft", "report", "post-mortem", "email",
      "doc", "thesis", "article"), "Write"),
    (("bug", "code", "pr", "review", "repo", "auth", "release", "slack",
      "deploy", "test"), "Open"),
    (("room", "laundry", "dishes", "desk", "pack", "clean", "clothes",
      "mess", "buried"), "Grab"),
    (("bill", "pay", "electricity", "train", "ticket", "book"), "Open"),
    (("pdf", "read", "research", "paper"), "Read"),
]

_CALM_TIPS = [
    "Ugly first drafts count. You can fix it later — you just need to start.",
    "Set a timer if it helps. When it rings, you are allowed to stop.",
    "Done is better than perfect. One tiny win beats a perfect plan.",
    "If your brain protests, make the step smaller, not the goal bigger.",
    "Breathe once, slowly, before you begin. Then just the first motion.",
    "You do not have to finish this. You only have to begin it.",
    "Put your phone face-down for this one step. The world can wait.",
    "If it feels hard, that means it matters — not that you are failing.",
]


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def _split_chunks(text, cap=8):
    """Split a messy brain dump into task-ish chunks, deterministically."""
    text = _clean(text)
    if not text:
        return []
    parts = []
    for line in re.split(r"[\n\r]+", text):
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip(" ,;:")
            if sentence:
                parts.append(sentence)
    chunks = []
    for part in parts:
        if len(part) > 70:
            for sub in re.split(r"\s*;\s*|\s*,\s+and\s+|\s+and\s+|\s*,\s+", part):
                sub = re.sub(r"^and\s+", "", sub.strip(" ,;:"))
                if len(sub) >= 3:
                    chunks.append(sub)
        else:
            chunks.append(part)
    seen, out = set(), []
    for chunk in chunks:
        key = chunk.lower()
        if key not in seen and len(chunk) >= 3:
            seen.add(key)
            out.append(chunk)
    return out[:cap]


_FEELING_RE = re.compile(
    r"\b(panic|panicking|anxious|anxiety|overwhelm|overwhelmed|stressed|"
    r"burnout|frozen|can't start|cannot start|don't know where to start)\b")
_CLEAR_MESS_RE = re.compile(
    r"^(?:my\s+)?(.+?)\s+(?:is|are)\s+(?:a\s+mess|buried|piled up)")


def _physical_title(raw):
    """Rewrite a raw chunk so it starts with a physical, friction-free verb."""
    raw = _clean(raw).rstrip(".")
    if not raw:
        return "Take one slow breath and begin"
    lowered = raw.lower()
    # Feelings are not tasks: turn panic/freeze statements into a calming step.
    if _FEELING_RE.search(lowered):
        return "Take one slow breath and name the smallest first move"
    clear = _CLEAR_MESS_RE.match(lowered)
    if clear:
        return "Clear the %s" % clear.group(1)
    # Strip personal lead-ins ("I need to…", "I forgot to…",
    # "I haven't written…") so the verb logic sees the real action.
    rest = re.sub(
        r"^(i have|i need|i must|i am|i'm|i haven't|i have not|i forgot to|i forgot)\s+",
        "", raw, flags=re.I)
    rest = re.sub(r"^to\s+", "", rest, flags=re.I)
    rest = re.sub(r"^(written|done|finished)\s+", "", rest, flags=re.I)
    rest = re.sub(r"\s+yet$", "", rest, flags=re.I)
    if not rest:
        return "Take one slow breath and begin"
    words = rest.split(" ")
    if words[0].lower().strip(",") in _PHYSICAL_VERBS and len(words) > 1:
        return rest[0].upper() + rest[1:]
    for keywords, verb in _VERB_BY_KEYWORD:
        if any(k in lowered for k in keywords):
            return "%s %s" % (verb, rest[0].lower() + rest[1:] if rest else "")
    return "Start %s" % (rest[0].lower() + rest[1:] if rest else "")


def _heuristic_decompose(brain_dump, energy_level):
    chunks = _split_chunks(brain_dump)
    if not chunks:
        chunks = ["take one small step on the task in front of you"]
    if energy_level == "low":
        durations = [1, 2]
    elif energy_level == "high":
        durations = [10, 15]
    else:
        durations = [5]
    steps = []
    for i, chunk in enumerate(chunks):
        title = _physical_title(chunk)
        if len(title) > 110:
            cut = title[:110].rsplit(" ", 1)[0]
            title = cut if cut else title[:110]
        steps.append({
            "id": "step-%d" % (i + 1),
            "title": title,
            "duration_minutes": durations[i % len(durations)],
            "energy": "Low" if energy_level in ("low", "medium") else "Medium",
            "tip": _CALM_TIPS[i % len(_CALM_TIPS)],
        })
    # Drop duplicate titles (e.g. two feeling chunks mapping to one breath step).
    seen_titles, unique_steps = set(), []
    for step in steps:
        if step["title"].lower() not in seen_titles:
            seen_titles.add(step["title"].lower())
            unique_steps.append(step)
    steps = unique_steps
    if energy_level == "low":
        empathy = ("This feels huge because a lot of separate things arrived at once. "
                   "We will take them one 1-minute step at a time — nothing more is asked of you.")
    elif energy_level == "high":
        empathy = ("You are carrying a full load, and it makes sense that it feels heavy. "
                   "We will turn it into clear, structured steps you can move through in flow.")
    else:
        empathy = ("It is completely normal for a pile like this to freeze anyone. "
                   "We will make each next move so small it is hard not to start.")
    traditional = _split_chunks(brain_dump, cap=15)
    return {
        "empathy_note": empathy,
        "traditional_cluttered_list": traditional[:15],
        "steps": steps,
        "source": "heuristic-fallback",
    }


def _heuristic_slice_smaller(step_title, context):
    title = _clean(step_title)
    verb_match = re.match(r"^(\w+)\s+(.*)$", title)
    if verb_match and verb_match.group(1).lower() in _PHYSICAL_VERBS:
        action = verb_match.group(2)
        verb = verb_match.group(1).capitalize()
    else:
        action = title
        verb = "Do"
    if " and " in action:
        action = action.split(" and ")[0]
    obj = action if len(action) <= 45 else action[:45].rsplit(" ", 1)[0]
    substeps = [
        {"id": "sub-1", "title": "Get ready: put %s in front of you" % obj,
         "duration_minutes": 1, "energy": "Low",
         "tip": "No doing yet. Just set the stage — that alone counts as progress."},
        {"id": "sub-2", "title": "%s the first tiny part of %s" % (verb, obj),
         "duration_minutes": 1, "energy": "Low",
         "tip": "Only 60 seconds. When the minute ends, you may stop with zero guilt."},
        {"id": "sub-3", "title": "Stop, take one slow breath, and mark this tiny win done",
         "duration_minutes": 1, "energy": "Low",
         "tip": "A finished baby step rewires the day. Let yourself feel it."},
    ]
    return {"substeps": substeps, "source": "heuristic-fallback"}


# ---------------------------------------------------------------------------
# Groq integration (with defensive parsing; any failure -> heuristic fallback)
# ---------------------------------------------------------------------------

def _groq_chat(system_prompt, user_text):
    if not GROQ_API_KEY:
        return None
    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": "Bearer %s" % GROQ_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception:
        return None


def _normalize_steps(raw_steps):
    steps = []
    if not isinstance(raw_steps, list):
        return steps
    for i, item in enumerate(raw_steps[:8]):
        if not isinstance(item, dict) or not item.get("title"):
            continue
        try:
            duration = int(item.get("duration_minutes", 5))
        except (TypeError, ValueError):
            duration = 5
        energy = item.get("energy", "Low")
        if energy not in ("Low", "Medium", "High"):
            energy = "Low"
        steps.append({
            "id": item.get("id") or "step-%d" % (i + 1),
            "title": str(item["title"])[:160],
            "duration_minutes": max(1, min(30, duration)),
            "energy": energy,
            "tip": str(item.get("tip", _CALM_TIPS[i % len(_CALM_TIPS)]))[:220],
        })
    return steps


def _groq_decompose(brain_dump, energy_level, persona):
    level_text = {"low": "low energy: 1-2 minute ultra-baby steps, survival mode",
                  "medium": "medium energy: 5 minute micro-steps, steady mode",
                  "high": "high energy: 10-15 minute structured steps, flow mode"}.get(
                      energy_level, "medium energy: 5 minute micro-steps")
    system = (
        "You are an ADHD and executive-function coach. Convert the user's messy "
        "brain dump into 5 to 8 concrete, non-intimidating micro-steps tailored "
        "to their energy level: %s. Every step MUST start with a physical, "
        "friction-free verb (Grab, Open, Write 1 sentence, etc.). Also return a "
        "1-sentence warm empathy note, and a 12-15 item intimidating raw task "
        "list (traditional_cluttered_list) showing how the same work looks as a "
        "cluttered old-style to-do list. Return STRICTLY valid JSON with keys: "
        "empathy_note, traditional_cluttered_list, steps (each step: id, title, "
        "duration_minutes, energy, tip). No markdown, no extra text." % level_text
    )
    user_text = "Persona: %s\nEnergy: %s\nBrain dump:\n%s" % (
        persona or "user", energy_level, brain_dump)
    data = _groq_chat(system, user_text)
    if not data:
        return None
    steps = _normalize_steps(data.get("steps"))
    if not steps:
        return None
    traditional = [str(x)[:160] for x in data.get("traditional_cluttered_list", [])
                   if isinstance(x, str) and x.strip()][:15]
    return {
        "empathy_note": str(data.get("empathy_note", ""))[:300] or None,
        "traditional_cluttered_list": traditional,
        "steps": steps,
        "source": "groq",
    }


def _groq_slice_smaller(step_title, context):
    system = (
        "You are an ADHD and executive-function coach. Break ONE intimidating "
        "step into exactly 3 ultra-tiny, 60-second physical actions. Each action "
        "must start with a physical verb and be doable in one minute. Return "
        "STRICTLY valid JSON: {\"substeps\": [{\"title\": str, "
        "\"duration_minutes\": 1, \"energy\": \"Low\", \"tip\": str}]}. No markdown."
    )
    data = _groq_chat(system, "Step: %s\nContext: %s" % (step_title, context or ""))
    if not data:
        return None
    subs = []
    for i, item in enumerate((data.get("substeps") or [])[:3]):
        if isinstance(item, dict) and item.get("title"):
            subs.append({
                "id": "sub-%d" % (i + 1),
                "title": str(item["title"])[:160],
                "duration_minutes": 1,
                "energy": "Low",
                "tip": str(item.get("tip", _CALM_TIPS[i % len(_CALM_TIPS)]))[:220],
            })
    return {"substeps": subs, "source": "groq"} if len(subs) == 3 else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/decompose", methods=["POST"])
def decompose():
    payload = request.get_json(silent=True) or {}
    brain_dump = _clean(payload.get("brain_dump", ""))
    if not brain_dump:
        return jsonify({"error": "brain_dump is required"}), 400
    energy = payload.get("energy_level", "medium")
    if energy not in ("low", "medium", "high"):
        energy = "medium"
    persona = _clean(payload.get("persona", ""))[:80]
    result = _groq_decompose(brain_dump, energy, persona)
    if result is None:
        result = _heuristic_decompose(brain_dump, energy)
    if not result.get("empathy_note"):
        result["empathy_note"] = _heuristic_decompose(brain_dump, energy)["empathy_note"]
    return jsonify(result)


@app.route("/api/slice-smaller", methods=["POST"])
def slice_smaller():
    payload = request.get_json(silent=True) or {}
    step_title = _clean(payload.get("step_title", ""))
    if not step_title:
        return jsonify({"error": "step_title is required"}), 400
    context = _clean(payload.get("context", ""))[:500]
    result = _groq_slice_smaller(step_title, context)
    if result is None:
        result = _heuristic_slice_smaller(step_title, context)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
