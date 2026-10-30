"""The fixed mood vocabulary and the 'lift me up' direction for each mood."""
from __future__ import annotations

from typing import Literal, get_args

Mood = Literal[
    "joyful", "sad", "anxious", "angry", "lonely", "drained", "nostalgic", "calm", "hopeful"
]
MOODS: tuple[str, ...] = get_args(Mood)

# "Feel understood" returns a capsule in the same mood.
# "Lift me up" moves one step toward something easier to be in.
LIFT: dict[str, str] = {
    "sad": "hopeful",
    "anxious": "calm",
    "angry": "calm",
    "lonely": "hopeful",
    "drained": "calm",
    "nostalgic": "joyful",
    "hopeful": "joyful",
    "calm": "joyful",
    "joyful": "joyful",
}


def target_mood(mood: str, mode: str) -> str:
    return LIFT[mood] if mode == "lift" else mood
