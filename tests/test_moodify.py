import asyncio
import json
from collections import Counter

import httpx
import pytest
from fastapi.testclient import TestClient

from moodify.app import create_app
from moodify.links import LinkInfo
from moodify.moderation import Moderator
from moodify.matcher import best_capsule
from moodify.moods import LIFT, MOODS
from moodify.reader import LexiconReader, LLMReader, in_crisis
from moodify.store import SEED_FILE, Store


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "test.db"), reader=LLMReader(api_key=""),
                                 moderator=Moderator(api_key=""), link_lookup=lambda link: LinkInfo(None, None, None)))


def fake_llm(content: str | None = None, status: int = 200) -> LLMReader:
    def handler(request: httpx.Request) -> httpx.Response:
        if content is None:
            raise httpx.ConnectTimeout("timed out")
        return httpx.Response(status, json={"choices": [{"message": {"content": content}}]})
    return LLMReader(api_key="test", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


# --- starter set -----------------------------------------------------------

def test_starter_set_has_200_capsules_covering_every_mood():
    starters = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    assert len(starters) == 200
    assert len({(c["song"], c["artist"]) for c in starters}) == 200  # no duplicates
    assert min(Counter(c["mood"] for c in starters).values()) >= 20
    assert {c["mood"] for c in starters} == set(MOODS)
    assert all(10 <= len(c["note"]) <= 280 for c in starters)


def test_every_lift_target_is_a_known_mood():
    assert set(LIFT) == set(MOODS) and set(LIFT.values()) <= set(MOODS)


def test_store_seeds_once_and_labels_starters(tmp_path):
    path = tmp_path / "s.db"
    Store(path)
    store = Store(path)  # second open must not seed again
    capsules = store.all()
    assert len(capsules) == 200
    assert {c.source for c in capsules} == {"starter"}
    assert {c.author for c in capsules} == {"MoodIfy starter set"}


def test_new_starters_reach_an_existing_database(tmp_path):
    path = tmp_path / "old.db"
    store = Store(path)
    with store._connect() as con:  # simulate a database seeded before the set grew
        con.execute("delete from capsules where id > 50")
    assert len(Store(path).all()) == 200


# --- mood reading ----------------------------------------------------------

@pytest.mark.parametrize("text,mood", [
    ("exam tomorrow and I can't stop overthinking", "anxious"),
    ("so tired after this long day, completely drained", "drained"),
    ("got the job!! best day ever", "joyful"),
    ("found old photos from school days", "nostalgic"),
])
def test_lexicon_reads_clear_moods(text, mood):
    assert LexiconReader().read(text).mood == mood


def test_lexicon_matches_word_starts_only():
    # "made" must not count as "mad", and "download" not as "down".
    assert LexiconReader().read("I made a playlist while the download finished").confidence == 0.0


def test_llm_label_is_used_when_valid():
    reading = asyncio.run(fake_llm('{"mood": "lonely"}').read("nobody texts me"))
    assert (reading.mood, reading.source) == ("lonely", "llm")


@pytest.mark.parametrize("reader", [
    fake_llm('{"mood": "ecstatic-ish"}'),   # label outside the list
    fake_llm("I think you feel tired"),     # no JSON
    fake_llm('{"mood": "joyful"}', 500),    # provider error
    fake_llm(None),                         # timeout
])
def test_llm_failures_fall_back_to_lexicon(reader):
    reading = asyncio.run(reader.read("so tired and burnt out"))
    assert (reading.mood, reading.source) == ("drained", "lexicon")


def test_slow_model_falls_back_at_the_deadline():
    async def slow(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(5)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"mood": "sad"}'}}]})
    reader = LLMReader(api_key="test", client=httpx.AsyncClient(transport=httpx.MockTransport(slow)), deadline=0.2)
    reading = asyncio.run(reader.read("so tired and burnt out"))
    assert (reading.mood, reading.source) == ("drained", "lexicon")

def test_crisis_phrases_are_detected():
    assert in_crisis("I want to die")
    assert in_crisis("thinking about self-harm again")
    assert not in_crisis("this exam is killing me")


# --- matching --------------------------------------------------------------

def test_matcher_prefers_capsules_whose_note_fits_the_text(tmp_path):
    capsules = Store(tmp_path / "m.db").all("anxious")
    capsule = best_capsule("can't sleep, mind racing at 2am", capsules, seen=set())
    assert capsule.song == "Breathe (2 AM)"


def test_matcher_skips_seen_capsules_until_pool_runs_out(tmp_path):
    capsules = Store(tmp_path / "m.db").all("calm")
    seen = {c.id for c in capsules[:-1]}
    assert best_capsule("anything", capsules, seen).id == capsules[-1].id
    assert best_capsule("anything", capsules, {c.id for c in capsules}) is not None


# --- API -------------------------------------------------------------------

def test_relate_returns_same_mood(client):
    body = client.post("/api/match", json={"text": "so lonely, nobody around", "mode": "relate"}).json()
    assert body["mood"] == body["target_mood"] == "lonely"
    assert body["capsule"]["mood"] == "lonely"


def test_lift_moves_toward_target(client):
    body = client.post("/api/match", json={"text": "anxious about my interview", "mode": "lift"}).json()
    assert (body["mood"], body["target_mood"], body["capsule"]["mood"]) == ("anxious", "calm", "calm")


def test_crisis_text_gets_support_and_never_reaches_a_model(tmp_path):
    calls = []
    reader = fake_llm('{"mood": "sad"}')
    reader.read = lambda text: calls.append(text)  # would record any model call
    client = TestClient(create_app(str(tmp_path / "c.db"), reader=reader, moderator=Moderator(api_key="")))
    body = client.post("/api/match", json={"text": "I want to end it all"}).json()
    assert "14416" in body["support"]
    assert body["source"] == "safety" and calls == []


def test_shared_capsule_is_matched_to_the_next_person(client):
    created = client.post("/api/capsules", json={
        "song": "Ocean Eyes", "artist": "Billie Eilish", "mood": "lonely",
        "note": "Helped me through my first lonely month in a new city", "name": "Asha",
    })
    assert created.status_code == 201
    assert created.json()["capsule"]["source"] == "community"
    body = client.post("/api/match", json={"text": "first month in a new city and so lonely"}).json()
    assert body["capsule"]["song"] == "Ocean Eyes"


@pytest.mark.parametrize("payload", [
    {"song": "x", "artist": "y", "mood": "happy-ish", "note": "a long enough note here"},
    {"song": "x", "artist": "y", "mood": "calm", "note": "short"},
    {"song": "x", "artist": "y", "mood": "calm", "note": "listen at https://spam.example now"},
])
def test_invalid_capsules_are_rejected(client, payload):
    assert client.post("/api/capsules", json=payload).status_code == 422


def test_index_page_is_served(client):
    assert "MoodIfy" in client.get("/").text
