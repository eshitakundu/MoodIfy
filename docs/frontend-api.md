# MoodIfy API for the frontend

All responses are JSON. Every text field is untrusted user input: render it with `textContent`, never `innerHTML`.

## Capsule object

Returned by matching, channels, the wall and sharing.

```json
{
  "id": 61,
  "title": "Ocean Eyes",              // ALWAYS present: song title, typed title, or the site name
  "artist": "Billie Eilish",          // may be null
  "site": "YouTube",                  // "YouTube", "Spotify", "SoundCloud"... or a bare domain like "my-band.net"; null for starter capsules
  "listen_url": "https://www.youtube.com/watch?v=...",   // ALWAYS present: the shared link, or a YouTube search for starter songs
  "thumbnail": "https://i.ytimg.com/...",                 // may be null
  "mood": "lonely",
  "note": "This got me through my first lonely month in a new city.",   // the message
  "author": "Asha",                   // "Anonymous" if no name
  "source": "community",              // or "starter"
  "created_at": "2026-10-30T14:02:11+00:00",
  "song": "Ocean Eyes", "url": "https://..."             // raw fields; prefer title / listen_url above
}
```

Show the domain for unknown sites (when `site` contains a dot) so people know where a link goes, and open links with `target="_blank" rel="noopener noreferrer"`.

## Share a song (cassette, then the flip side)

`POST /api/capsules`

```json
{ "url": "https://soundcloud.com/...", "message": "why this song, 10-400 characters", "title": "optional, max 120", "name": "optional, max 40" }
```

Collect the link on the front of the cassette and the message on the flipped side, then send **one** request at the end. The mood is worked out from the message; you can also send `"mood"` if you add a picker.

Response `201`:

```json
{ "status": "visible" | "held" | "crisis", "message": "text to show the person", "capsule": { ... } | null, "support": "helpline text" | null }
```

- `visible`: it's live. `capsule` is the saved capsule, so you can add it straight to the wall.
- `held`: saved but waiting for review (the moderator was unsure, or it contained a link or contact details). Show `message`. Don't add it to the wall.
- `crisis`: the message mentioned self-harm. It is NOT posted. Show `support` prominently and gently.

Errors:
- `422` with `detail` as a **string** for link problems ("Use an https:// link.", "That doesn't look like a public link."), or as a **list** of `{msg}` for field problems (missing message, links inside the message, too long). Show `detail` if it's a string, otherwise `detail[0].msg` with a leading "Value error, " removed.
- `429` (`detail` string) when someone has shared 3 songs in an hour or 10 in a day.

The old form shape `{song, artist, mood, note, name}` still works, so the current page keeps working until the new one replaces it.

## Wall of messages

`GET /api/wall?limit=20` returns community capsules, newest first (starter capsules never appear here).
`GET /api/wall?before=<id of the last one you have>&limit=20` returns the next page. An empty list means the end.

## Unchanged

- `POST /api/match` with `{text, mode: "relate" | "lift", seen: [ids]}` returns `{mood, target_mood, source, capsule, support}`.
- `GET /api/capsules?mood=calm` returns that channel's capsules.
- `GET /api/moods` returns the 9 moods.

Use `capsule.title` and `capsule.listen_url` in the result card instead of `song` and a search link.
