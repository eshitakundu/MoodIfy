"""Song links: validate them, recognise the site, and look up a title.

Capsules can point anywhere (YouTube, Spotify, SoundCloud, an unreleased demo on
Drive), so the rules are about safety rather than an allowlist:
  * https only, no credentials in the URL, no IP addresses or localhost
  * known music sites are labelled by name; anything else is marked "external"
    so the page can show the domain clearly before someone clicks it
Titles come from the site's public oEmbed endpoint (no API key). If that fails,
the capsule falls back to the title the person typed, then to the site name.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

MAX_URL = 500

# hostname suffix -> display name
KNOWN_SITES = {
    "youtube.com": "YouTube", "youtu.be": "YouTube", "music.youtube.com": "YouTube Music",
    "open.spotify.com": "Spotify", "spotify.link": "Spotify",
    "soundcloud.com": "SoundCloud", "on.soundcloud.com": "SoundCloud",
    "bandcamp.com": "Bandcamp", "music.apple.com": "Apple Music",
    "audiomack.com": "Audiomack", "deezer.com": "Deezer", "tidal.com": "TIDAL",
    "jiosaavn.com": "JioSaavn", "gaana.com": "Gaana", "wynk.in": "Wynk",
    "drive.google.com": "Google Drive", "dropbox.com": "Dropbox",
}

# Sites with a public oEmbed endpoint that returns a title without a key.
OEMBED = {
    "YouTube": "https://www.youtube.com/oembed?format=json&url={url}",
    "YouTube Music": "https://www.youtube.com/oembed?format=json&url={url}",
    "Spotify": "https://open.spotify.com/oembed?url={url}",
    "SoundCloud": "https://soundcloud.com/oembed?format=json&url={url}",
}


class LinkError(ValueError):
    """The link can't be accepted; the message is safe to show to the user."""


@dataclass(frozen=True)
class SongLink:
    url: str
    host: str
    site: str          # "YouTube", "Spotify", ... or the bare domain for unknown sites
    known: bool


def _site_for(host: str) -> tuple[str, bool]:
    for suffix, name in KNOWN_SITES.items():
        if host == suffix or host.endswith("." + suffix):
            return name, True
    return host, False


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def parse_link(raw: str) -> SongLink:
    value = (raw or "").strip()
    if not value:
        raise LinkError("Add a link to the song.")
    if len(value) > MAX_URL:
        raise LinkError("That link is too long.")
    scheme = re.match(r"^([a-z][a-z0-9+.-]*):", value, re.I)
    if scheme and scheme.group(1).lower() != "https" and "://" not in value:
        raise LinkError("Use an https:// link.")  # javascript:, data:, mailto: and friends
    if "://" not in value:
        value = "https://" + value
    parts = urlsplit(value)
    if parts.scheme != "https":
        raise LinkError("Use an https:// link.")
    if parts.username or parts.password:
        raise LinkError("Links can't contain a username or password.")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or "." not in host or host == "localhost" or host.endswith(".local"):
        raise LinkError("That doesn't look like a public link.")
    if _is_ip(host):
        raise LinkError("Use a site link, not an IP address.")
    if host.startswith("www."):
        host = host[4:]
    site, known = _site_for(host)
    clean = urlunsplit(("https", parts.netloc.lower(), parts.path or "/", parts.query, ""))
    return SongLink(url=clean, host=host, site=site, known=known)


@dataclass(frozen=True)
class LinkInfo:
    title: str | None
    artist: str | None
    thumbnail: str | None


def lookup(link: SongLink, client: httpx.Client | None = None) -> LinkInfo:
    """Best effort: a title and artist from the site's oEmbed, or nothing."""
    endpoint = OEMBED.get(link.site)
    if not endpoint:
        return LinkInfo(None, None, None)
    client = client or httpx.Client(timeout=6, follow_redirects=True)
    try:
        response = client.get(endpoint.format(url=quote(link.url, safe="")))
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return LinkInfo(None, None, None)
    title = (data.get("title") or "").strip()[:160] or None
    artist = (data.get("author_name") or "").strip()[:120] or None
    thumbnail = data.get("thumbnail_url") if str(data.get("thumbnail_url", "")).startswith("https://") else None
    return LinkInfo(title, artist, thumbnail)


def search_link(song: str, artist: str) -> str:
    """For capsules without a link (the starter set): a YouTube search for the song."""
    return "https://www.youtube.com/results?search_query=" + quote(f"{song} {artist}")
