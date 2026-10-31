import asyncio
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from moodify.app import create_app
from moodify.links import LinkError, LinkInfo, lookup, parse_link
from moodify.moderation import Moderator, rule_check
from moodify.reader import LLMReader
from moodify.store import Store

GOOD_NOTE = "This got me through my first lonely month in a new city."


def moderator_replying(content: str | None) -> Moderator:
    def handler(request: httpx.Request) -> httpx.Response:
        if content is None:
            raise httpx.ConnectTimeout("down")
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    return Moderator(api_key="k", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def make_client(tmp_path, moderator=None, info=LinkInfo("Ocean Eyes", "Billie Eilish", "https://i.ytimg.com/x.jpg"),
                monkeypatch=None, admin_token=None):
    if monkeypatch and admin_token:
        monkeypatch.setenv("MOODIFY_ADMIN_TOKEN", admin_token)
    app = create_app(str(tmp_path / "t.db"), reader=LLMReader(api_key=""),
                     moderator=moderator or Moderator(api_key=""), link_lookup=lambda link: info)
    return TestClient(app)


def share(client, **overrides):
    body = {"url": "https://www.youtube.com/watch?v=abc", "message": GOOD_NOTE, "name": "Asha", **overrides}
    return client.post("/api/capsules", json=body)


# --- links -----------------------------------------------------------------

@pytest.mark.parametrize("raw,site,known", [
    ("https://www.youtube.com/watch?v=abc", "YouTube", True),
    ("youtu.be/abc", "YouTube", True),
    ("https://open.spotify.com/track/1", "Spotify", True),
    ("https://soundcloud.com/artist/demo-unreleased", "SoundCloud", True),
    ("https://someband.bandcamp.com/track/x", "Bandcamp", True),
    ("https://drive.google.com/file/d/1/view", "Google Drive", True),
    ("https://my-friends-band.net/songs/1", "my-friends-band.net", False),
])
def test_links_are_normalised_and_labelled(raw, site, known):
    link = parse_link(raw)
    assert link.url.startswith("https://") and link.site == site and link.known is known


@pytest.mark.parametrize("raw,reason", [
    ("http://example.com/song", "https"),
    ("javascript:alert(1)", "https"),
    ("https://user:pw@example.com/x", "password"),
    ("https://127.0.0.1/x", "IP address"),
    ("https://localhost/x", "public link"),
    ("", "Add a link"),
])
def test_unsafe_links_are_rejected(raw, reason):
    with pytest.raises(LinkError, match=reason):
        parse_link(raw)


def test_lookup_reads_oembed_and_survives_failures():
    ok = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={
        "title": "Ocean Eyes", "author_name": "Billie Eilish", "thumbnail_url": "https://i.ytimg.com/a.jpg"})))
    assert asyncio.run(lookup(parse_link("youtu.be/x"), ok)) == LinkInfo("Ocean Eyes", "Billie Eilish", "https://i.ytimg.com/a.jpg")
    down = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    assert asyncio.run(lookup(parse_link("youtu.be/x"), down)) == LinkInfo(None, None, None)
    assert asyncio.run(lookup(parse_link("https://my-band.net/x"))) == LinkInfo(None, None, None)  # no oEmbed: no request


# --- moderation ------------------------------------------------------------

@pytest.mark.parametrize("text,status", [
    ("I want to end it all tonight", "crisis"),
    ("follow me at insta dot com, link: mysite.com", "held"),
    ("call me on +91 98765 43210 anytime", "held"),
    ("BUY CHEAP FOLLOWERS NOW BEST PRICES GUARANTEED", "held"),
    ("sooooooooooo good", "held"),
])
def test_rules_catch_obvious_problems(text, status):
    assert rule_check(text).status == status


def test_rules_pass_ordinary_sad_messages():
    assert rule_check("I felt so alone after the breakup and this song helped") is None


@pytest.mark.parametrize("reply,status", [
    ('{"verdict": "ok", "reason": "kind"}', "visible"),
    ('{"verdict": "hold", "reason": "harassment"}', "held"),
    ("I think this is fine", "held"),   # unparseable: held, not published
    (None, "held"),                    # model down: held, not published
])
def test_llm_moderation_fails_closed(reply, status):
    assert asyncio.run(moderator_replying(reply).check(GOOD_NOTE)).status == status


def test_missing_key_holds_everything_when_moderation_is_required(monkeypatch):
    monkeypatch.setenv("MOODIFY_REQUIRE_MODERATION", "1")
    assert asyncio.run(Moderator(api_key="").check(GOOD_NOTE)).status == "held"


# --- sharing by link ---------------------------------------------------------

def test_link_capsule_gets_title_site_and_inferred_mood(tmp_path):
    body = share(make_client(tmp_path)).json()
    assert body["status"] == "visible"
    capsule = body["capsule"]
    assert (capsule["title"], capsule["artist"], capsule["site"]) == ("Ocean Eyes", "Billie Eilish", "YouTube")
    assert capsule["listen_url"] == "https://www.youtube.com/watch?v=abc"
    assert capsule["mood"] == "lonely"  # read from the message, nobody picked it


def test_unknown_link_falls_back_to_typed_title_then_site(tmp_path):
    client = make_client(tmp_path, info=LinkInfo(None, None, None))
    typed = share(client, url="https://my-band.net/demo", title="Demo 3 (unreleased)").json()["capsule"]
    assert typed["title"] == "Demo 3 (unreleased)"
    bare = share(client, url="https://my-band.net/demo2", name="Ravi").json()["capsule"]
    assert bare["title"] == "my-band.net"


def test_link_and_message_are_both_required(tmp_path):
    client = make_client(tmp_path)
    assert client.post("/api/capsules", json={"url": "https://youtu.be/x"}).status_code == 422
    assert client.post("/api/capsules", json={"message": GOOD_NOTE}).status_code == 422
    assert share(client, url="http://insecure.com/x").status_code == 422
    assert share(client, message="listen here https://spam.example now please").status_code == 422


def test_held_and_crisis_capsules_never_reach_matching_or_the_wall(tmp_path):
    client = make_client(tmp_path, moderator=moderator_replying('{"verdict": "hold", "reason": "ads"}'))
    held = share(client).json()
    assert held["status"] == "held" and held["capsule"] is None
    crisis = share(client, message="I don't want to live anymore and nothing helps").json()
    assert crisis["status"] == "crisis" and "14416" in crisis["support"]
    assert client.get("/api/wall").json() == []
    assert all(c["source"] == "starter" for c in client.get("/api/capsules").json())


def test_rate_limit_per_visitor(tmp_path):
    client = make_client(tmp_path)
    codes = [share(client, url=f"https://youtu.be/{i}").status_code for i in range(4)]
    assert codes == [201, 201, 201, 429]


# --- wall ------------------------------------------------------------------

def test_wall_is_community_only_newest_first_and_paginates(tmp_path):
    client = make_client(tmp_path)
    for i in range(3):
        share(client, url=f"https://youtu.be/{i}", name=f"P{i}")
    first = client.get("/api/wall", params={"limit": 2}).json()
    assert [c["author"] for c in first] == ["P2", "P1"]
    rest = client.get("/api/wall", params={"before": first[-1]["id"], "limit": 2}).json()
    assert [c["author"] for c in rest] == ["P0"]
    assert "submitter" not in first[0] and "moderation" not in first[0]


# --- admin -----------------------------------------------------------------

def test_admin_can_approve_and_hide_with_token_only(tmp_path, monkeypatch):
    client = make_client(tmp_path, moderator=moderator_replying('{"verdict": "hold", "reason": "unsure"}'),
                         monkeypatch=monkeypatch, admin_token="s3cret")
    share(client)
    assert client.get("/api/admin/capsules").status_code == 404
    held = client.get("/api/admin/capsules", headers={"Authorization": "Bearer s3cret"}).json()
    assert len(held) == 1 and held[0]["moderation"] == "llm: unsure"
    capsule_id = held[0]["id"]
    approve = client.post(f"/api/admin/capsules/{capsule_id}", json={"status": "visible"},
                          headers={"Authorization": "Bearer s3cret"})
    assert approve.status_code == 200 and len(client.get("/api/wall").json()) == 1
    client.post(f"/api/admin/capsules/{capsule_id}", json={"status": "hidden"}, headers={"Authorization": "Bearer s3cret"})
    assert client.get("/api/wall").json() == []


def test_admin_is_off_without_a_token(tmp_path, monkeypatch):
    monkeypatch.delenv("MOODIFY_ADMIN_TOKEN", raising=False)
    client = make_client(tmp_path)
    assert client.get("/api/admin/capsules", headers={"Authorization": "Bearer "}).status_code == 404


# --- migration -------------------------------------------------------------

def test_v1_database_is_upgraded_in_place(tmp_path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("create table capsules (id integer primary key autoincrement, song text not null, artist text not null,"
                " mood text not null, note text not null, author text not null, source text not null, created_at text not null)")
    con.execute("insert into capsules (song, artist, mood, note, author, source, created_at) values"
                " ('Old Song', 'Old Artist', 'calm', 'a note from before the upgrade', 'Mira', 'community', '2026-01-01')")
    con.commit(); con.close()
    capsules = [c for c in Store(path).all() if c.source == "community"]  # starters get topped up too
    assert [(c.title, c.author) for c in capsules] == [("Old Song", "Mira")]
    assert capsules[0].listen_url.startswith("https://www.youtube.com/results?search_query=")


def test_cassette_colour_is_saved_and_checked(tmp_path):
    client = make_client(tmp_path)
    saved = share(client, color="mint").json()["capsule"]
    assert saved["color"] == "mint" and client.get("/api/wall").json()[0]["color"] == "mint"
    assert share(client, url="https://youtu.be/other", color="neon-plaid").status_code == 422
    assert share(client, url="https://youtu.be/third").json()["capsule"]["color"] is None
