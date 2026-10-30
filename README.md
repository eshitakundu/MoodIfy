# MoodIfy

[![CI](https://github.com/eshitakundu/MoodIfy/actions/workflows/ci.yml/badge.svg)](https://github.com/eshitakundu/MoodIfy/actions/workflows/ci.yml)

**Tell it how you feel. Get back a song someone shared for that feeling, and the reason they shared it.**

People leave "mood capsules": a song, the mood it's for, and a line about why it helps. When you describe how you feel, MoodIfy reads your mood, then finds the capsule whose note fits your words best. You can ask to *feel understood* (same mood) or to be *lifted up* (a gentler mood one step away).

![MoodIfy matching "exam tomorrow and I can't stop overthinking" to a capsule about overthinking](docs/screenshot.png)

## How it works

```
your text ──► crisis check ──► mood reader ──► target mood ──► retrieval ──► capsule
                  │              LLM, falls      relate: same     TF-IDF over the
                  │              back to         lift: one step   target mood's
                  ▼              keywords        toward calm      notes, skips seen
          support message
          (never sent to a model)
```

1. **Mood reader.** An OpenRouter model labels the text with one of nine moods (joyful, sad, anxious, angry, lonely, drained, nostalgic, calm, hopeful). Its answer is validated against that fixed list. No key, a timeout, bad JSON or an unknown label all fall back to an offline keyword reader, so the app always answers.
2. **Retrieval.** Capsules are filtered to the target mood, then ranked by TF-IDF cosine similarity between your text and each capsule's note. "Can't sleep, mind racing at 2am" finds the capsule written for 2am anxiety, not just any anxious song. Community capsules win ties over starter ones, and you won't see the same capsule twice until the pool runs out.
3. **Safety first.** Text that mentions self-harm or suicide is never sent to a model. The response leads with a support message and free helplines (Tele-MANAS 14416 in India, findahelpline.com elsewhere).

### Starter set

A new community app is empty on day one, so MoodIfy ships with **50 starter capsules** across all nine moods, written by me and clearly labelled "MoodIfy starter set" in the UI and the API. Capsules people share are stored as `community` and preferred when they fit equally well.

## Evaluation

`python evals/run_eval.py` scores the mood reader on two labelled sets:

| Set | Cases | Offline keyword reader |
|---|---:|---:|
| Direct phrasing ("exam tomorrow and I'm so nervous") | 45 | 100% |
| Indirect phrasing ("refreshing the results page every two minutes") | 18 | 6% |

Read this honestly. I wrote the direct set alongside the keyword list, so 100% there only proves the fallback works on plain language, and CI fails if it drops below 85%. The indirect set is the real test: people rarely name their feelings, and keywords almost never catch that. That gap is what the LLM reader is for. Run `python evals/run_eval.py --llm` with an `OPENROUTER_API_KEY` to score it on the same cases.

## Tests

24 pytest tests cover the starter set, the reader (including every LLM failure mode falling back correctly, using a mocked transport), retrieval ranking and repeat-skipping, the API, crisis handling (asserting the model is never called), and capsule validation (mood list, length, no links).

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

uvicorn moodify.app:create_app --factory --reload    # http://localhost:8000
pytest -q
python evals/run_eval.py
```

Optional: set `OPENROUTER_API_KEY` (free at openrouter.ai) to use the LLM reader, and `MOODIFY_MODEL` to pick a model (default `openrouter/auto`). Without a key everything still works on the keyword reader.

## API

| Method | Path | What it does |
|---|---|---|
| `POST` | `/api/match` | `{text, mode: "relate" or "lift", seen: [ids]}` returns the reading and a capsule |
| `POST` | `/api/capsules` | Share a capsule: `{song, artist, mood, note, name?}` |
| `GET` | `/api/capsules?mood=calm` | List capsules, optionally by mood |
| `GET` | `/api/moods` | The nine moods |

Interactive docs at `/docs`.

## Limitations

- Keyword fallback is weak on indirect language (see the eval). With no API key, expect generic matches for subtle text.
- No accounts or rate limiting yet. Submissions are validated for mood, length and links, not moderated by a person.
- One mood per message. Mixed feelings ("happy but scared") get the stronger signal.

## History

Started in March 2025 as a hackathon prototype (Streamlit, MySQL and a UiPath email workflow), which grew out of the capsule idea in [Trackify](https://github.com/eshitakundu/Trackify). Rebuilt in October 2026 as a tested FastAPI service with an LLM mood reader, retrieval and evals. The earlier commits are still in the history.

## Stack

Python · FastAPI · Pydantic · SQLite · httpx · OpenRouter · vanilla JS · pytest · GitHub Actions
