"""Pick the capsule that best fits what someone wrote.

Retrieval is two-stage:
  1. Filter to capsules in the target mood (same mood, or the "lift" mood).
  2. Rank those by TF-IDF cosine similarity between the user's text and each
     capsule's song, artist and note, so "exam tomorrow" prefers a capsule
     whose note talks about exams.
Community capsules win ties over starter ones, and capsules the person has
already seen are skipped until the pool runs out.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .store import Capsule

TOKEN = re.compile(r"[a-z']+")
STOP = frozenset(
    "a an the and or but i i'm im me my you your it it's is am are was were be been to of in on at "
    "for with so just really very this that these those when what feel feeling like have has had "
    "do does did not no can can't cant will would".split()
)


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 2]


def _tfidf(docs: list[list[str]]) -> tuple[list[dict[str, float]], dict[str, float]]:
    df = Counter(term for doc in docs for term in set(doc))
    n = len(docs)
    idf = {term: math.log((1 + n) / (1 + count)) + 1 for term, count in df.items()}
    vectors = []
    for doc in docs:
        tf = Counter(doc)
        vectors.append({term: count * idf[term] for term, count in tf.items()})
    return vectors, idf


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(weight * b.get(term, 0.0) for term, weight in a.items())
    norm = math.sqrt(sum(w * w for w in a.values())) * math.sqrt(sum(w * w for w in b.values()))
    return dot / norm if norm else 0.0


def best_capsule(text: str, capsules: list[Capsule], seen: set[int]) -> Capsule | None:
    if not capsules:
        return None
    pool = [c for c in capsules if c.id not in seen] or capsules
    docs = [tokens(f"{c.song} {c.artist} {c.note}") for c in pool]
    vectors, idf = _tfidf(docs)
    query = {term: count * idf.get(term, 0.0) for term, count in Counter(tokens(text)).items()}
    ranked = sorted(
        zip(pool, vectors),
        key=lambda pair: (-_cosine(query, pair[1]), pair[0].source != "community", pair[0].id),
    )
    return ranked[0][0]
