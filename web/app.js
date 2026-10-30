const seen = [];
let lastRequest = { kind: "text", mode: "relate" };
let currentCapsule = null;
const $ = (id) => document.getElementById(id);
const MOOD_COLORS = { joyful: "#9a632a", sad: "#394a57", anxious: "#51495f", angry: "#7b312b", lonely: "#3d5554", drained: "#635d52", nostalgic: "#73503c", calm: "#486555", hopeful: "#8b6534" };
const LIGHTER = { calm: "calmer", joyful: "brighter", hopeful: "more hopeful" };
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function updateClock() {
  const now = new Date();
  $("clock").textContent = [now.getHours(), now.getMinutes(), now.getSeconds()].map((part) => String(part).padStart(2, "0")).join(":");
}
updateClock();
setInterval(updateClock, 1000);

// Every set cuts between clips like a late-night broadcast switcher.
// All clips live in one reel (media/reel.mp4, index in reel.json), fetched once and shared by
// every TV. A cut is a jump inside the reel, so screens never go black while a new file loads.
const channelVideos = [...document.querySelectorAll(".tv video, .cave-screen video")];

// The room drifts a little with the pointer; the sets in front move more, which reads as depth.
const caveRoom = document.querySelector(".cave-room");
if (caveRoom && !reducedMotion && matchMedia("(hover: hover) and (min-width: 901px)").matches) {
  const layer = caveRoom.querySelector(".cave-layer");
  const front = caveRoom.querySelectorAll(".tv-checkin, .tv-guide");
  caveRoom.addEventListener("pointermove", (event) => {
    const box = caveRoom.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    layer.style.transform = `translate(${-x * 14}px, ${-y * 9}px)`;
    front.forEach((set) => { set.style.transform = `translate(${-x * 30}px, ${-y * 16}px)`; });
  });
  caveRoom.addEventListener("pointerleave", () => {
    layer.style.transform = "";
    front.forEach((set) => { set.style.transform = ""; });
  });
}
const shouldPlay = (video) => !reducedMotion && video.dataset.visible !== "false" && !document.hidden;
// Slow enough to see the rain and drifting layers before the channel changes.
const cutInterval = () => 2500 + Math.random() * 1500;
const CLIP_COUNT = 20;  // media/clips/clip-01.mp4 … clip-20.mp4, made by scripts/render_pixel_reel.py
// Which scene each set is showing, so no two sets show the same one at once.
const onAir = new Map();
const pickScene = (video, count) => {
  const busy = new Set([...onAir].filter(([other]) => other !== video).map(([, scene]) => scene));
  const free = [...Array(count).keys()].filter((scene) => !busy.has(scene));
  const pool = free.length ? free : [...Array(count).keys()];
  const scene = pool[Math.floor(Math.random() * pool.length)];
  onAir.set(video, scene);
  return scene;
};

function runChannels(src, segments) {
  channelVideos.forEach((video) => {
    video.loop = true;
    const cut = () => {
      const seg = segments[pickScene(video, segments.length)];
      video.currentTime = seg.start + Math.random() * Math.max(0, seg.duration - 4.1);  // room for the longest cut
    };
    video.addEventListener("loadedmetadata", () => { cut(); if (shouldPlay(video)) video.play().catch(() => {}); }, { once: true });
    video.addEventListener("pause", () => { if (shouldPlay(video)) video.play().catch(() => {}); });
    video.src = src;
    if (reducedMotion) return;
    const flip = () => {
      if (shouldPlay(video) && video.readyState >= 1) cut();
      setTimeout(flip, cutInterval());
    };
    setTimeout(flip, 500 + Math.random() * 700);
  });
}

// Fallback if the reel can't load: the individual clips, one file per cut.
function runClips() {
  const clipUrl = (n) => `/media/clips/clip-${String(n).padStart(2, "0")}.mp4`;
  channelVideos.forEach((video) => {
    video.loop = true;
    const tune = () => { video.src = clipUrl(1 + pickScene(video, CLIP_COUNT)); if (shouldPlay(video)) video.play().catch(() => {}); };
    video.addEventListener("error", tune);
    tune();
    if (reducedMotion) return;
    const flip = () => { if (shouldPlay(video)) tune(); setTimeout(flip, cutInterval()); };
    setTimeout(flip, 500 + Math.random() * 700);
  });
}

Promise.all([
  fetch("/media/reel.json").then((r) => { if (!r.ok) throw new Error(); return r.json(); }),
  fetch("/media/reel.mp4").then((r) => { if (!r.ok) throw new Error(); return r.blob(); }),
]).then(([index, blob]) => runChannels(URL.createObjectURL(blob), index.segments)).catch(runClips);
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(({ isIntersecting, target }) => {
      target.dataset.visible = String(isIntersecting);
      if (isIntersecting && !reducedMotion) target.play().catch(() => {});
      else target.pause();
    });
  }, { rootMargin: "80px" });
  channelVideos.forEach((video) => observer.observe(video));
}
document.addEventListener("visibilitychange", () => {
  channelVideos.forEach((video) => {
    if (document.hidden) video.pause();
    else if (video.dataset.visible === "true" && !reducedMotion) video.play().catch(() => {});
  });
});

function setListenLinks(capsule) {
  const query = encodeURIComponent(`${capsule.title || capsule.song} ${capsule.artist || ""}`.trim());
  const shared = Boolean(capsule.url);
  $("listen-youtube").href = capsule.listen_url || `https://www.youtube.com/results?search_query=${query}`;
  $("listen-youtube").textContent = shared ? `OPEN ON ${capsule.site.toUpperCase()} ↗` : "LISTEN ON YOUTUBE ↗";
  $("listen-spotify").href = `https://open.spotify.com/search/${query}`;
  $("listen-spotify").classList.toggle("hidden", shared);
}
function showCapsule(capsule, reading, support) {
  currentCapsule = capsule;
  if (!seen.includes(capsule.id)) seen.push(capsule.id);
  $("support").textContent = support || "";
  $("support").classList.toggle("hidden", !support);
  $("reading").textContent = reading;
  $("song").textContent = capsule.title || capsule.song;
  $("artist").textContent = capsule.artist || capsule.site || "Community transmission";
  $("note").textContent = capsule.note;
  $("author").textContent = `Shared by ${capsule.author}`;
  document.querySelector(".result-art").style.setProperty("--mood-color", MOOD_COLORS[capsule.mood] || "#5c5043");
  setListenLinks(capsule);
  const disc = document.querySelector(".disc");
  disc.classList.remove("drop");
  void disc.offsetWidth;
  disc.classList.add("drop");
  const result = $("result");
  result.classList.remove("hidden");
  result.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
  result.focus({ preventScroll: true });
}
function setBusy(isBusy) {
  document.querySelectorAll("[data-mode], #random-channel, #another").forEach((button) => { button.disabled = isBusy; });
}
async function findByText(mode) {
  const text = $("feeling").value.trim();
  if (text.length < 3) {
    $("match-status").textContent = "Write a few words about how you feel first.";
    return $("feeling").focus();
  }
  lastRequest = { kind: "text", mode };
  $("match-status").textContent = "Tuning in…";
  setBusy(true);
  try {
    const response = await fetch("/api/match", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, mode, seen }) });
    if (!response.ok) throw new Error();
    const data = await response.json();
    if (!data.capsule) throw new Error();
    const reading = data.source === "safety" ? "A gentle song for right now" : data.target_mood !== data.mood
      ? `You sound ${data.mood}. Here's something a little ${LIGHTER[data.target_mood] || data.target_mood}`
      : `You sound ${data.mood}. Someone left this for that feeling`;
    $("match-status").textContent = "";
    showCapsule(data.capsule, reading, data.support);
  } catch {
    $("match-status").textContent = "Couldn't reach the song shelf. Try again in a moment.";
  } finally { setBusy(false); }
}
async function findRandomChannel() {
  lastRequest = { kind: "random" };
  const guide = document.querySelector(".tv-guide .screen");  // a burst of static as the set retunes
  guide.classList.remove("static");
  void guide.offsetWidth;
  guide.classList.add("static");
  $("match-status").textContent = "Scanning the community frequency…";
  setBusy(true);
  try {
    const response = await fetch("/api/capsules");
    if (!response.ok) throw new Error();
    const capsules = await response.json();
    const fresh = capsules.filter((capsule) => !seen.includes(capsule.id));
    const pool = fresh.length ? fresh : capsules;
    if (!pool.length) throw new Error();
    showCapsule(pool[Math.floor(Math.random() * pool.length)], "Random frequency found", null);
    $("match-status").textContent = "";
  } catch {
    $("match-status").textContent = "The frequency dropped out. Try again.";
  } finally { setBusy(false); }
}
document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => findByText(button.dataset.mode)));
$("random-channel").addEventListener("click", findRandomChannel);
// Now playing: songs people shared, topped up with starter songs while the community is small.
const shuffle = (list) => list.map((item) => [Math.random(), item]).sort((a, b) => a[0] - b[0]).map(([, item]) => item);
async function loadTicker() {
  try {
    const shared = shuffle(await (await fetch("/api/wall?limit=20")).json()).slice(0, 12);
    let picks = shared;
    if (shared.length < 12) {
      const starters = (await (await fetch("/api/capsules")).json()).filter((capsule) => capsule.source === "starter");
      picks = shuffle([...shared, ...shuffle(starters).slice(0, 12 - shared.length)]);
    }
    if (!picks.length) return;
    const items = picks.map((capsule) => {
      const item = document.createElement("span");
      const title = document.createElement("b");
      title.textContent = capsule.title || capsule.song;
      const showArtist = capsule.artist && !title.textContent.toLowerCase().includes(capsule.artist.toLowerCase());
      const credit = capsule.source === "starter" ? "from the starter set" : `shared by ${capsule.author}`;
      item.append("♪ ", title, `${showArtist ? ` — ${capsule.artist}` : ""} · ${credit}`);
      return item;
    });
    // Two copies so the crawl loops without a gap.
    $("np-items").replaceChildren(...items, ...items.map((item) => item.cloneNode(true)));
    $("np-items").style.setProperty("--np-time", `${picks.length * 7}s`);
  } catch { /* the strip just stays empty */ }
}
loadTicker();
$("another").addEventListener("click", () => lastRequest.kind === "random" ? findRandomChannel() : findByText(lastRequest.mode));
$("copy-capsule").addEventListener("click", async () => {
  if (!currentCapsule) return;
  const text = `“${currentCapsule.title || currentCapsule.song}”${currentCapsule.artist ? ` by ${currentCapsule.artist}` : ""}\n\n${currentCapsule.note}\n\nFound on MoodIfy`;
  try {
    await navigator.clipboard.writeText(text);
    $("copy-capsule").textContent = "COPIED ✓";
    setTimeout(() => { $("copy-capsule").textContent = "COPY THIS SONG"; }, 1800);
  } catch { $("copy-capsule").textContent = "COPY NOT AVAILABLE"; }
});

// One form, two physical sides. Nothing is posted until the message side is signed.
const shareForm = $("share");
const flipper = $("cassette-flipper");
// Phones show both sides as one form (see style.css), so neither side is ever hidden there.
const phone = matchMedia("(max-width: 600px)");
let cassetteSide = "front";
function setCassetteSide(side) {
  cassetteSide = side;
  flipper.classList.toggle("is-flipped", side === "back");
  flipper.querySelector(".cassette-front").inert = side === "back" && !phone.matches;
  flipper.querySelector(".cassette-back").inert = side !== "back" && !phone.matches;
}
setCassetteSide("front");
phone.addEventListener("change", () => setCassetteSide(cassetteSide));
$("flip-cassette").addEventListener("click", () => {
  const link = shareForm.elements.url.value.trim();
  if (!link || /\s/.test(link) || !link.includes(".")) {
    $("share-status").textContent = "Paste a link to the song, like youtu.be/… or open.spotify.com/…";
    return shareForm.elements.url.focus();
  }
  $("share-status").textContent = "";
  setCassetteSide("back");
  setTimeout(() => shareForm.elements.message.focus(), reducedMotion ? 0 : 420);
});
$("back-to-details").addEventListener("click", () => setCassetteSide("front"));

function makeWallNote(capsule) {
  const article = document.createElement("article");
  article.className = "wall-note tv";
  const head = document.createElement("span");
  head.className = "note-head";
  const channel = document.createElement("span");
  channel.textContent = `CH ${String(capsule.id).padStart(3, "0")}`;
  const mood = document.createElement("b");
  mood.textContent = (capsule.mood || "").toUpperCase();
  head.append(channel, mood);
  const message = document.createElement("blockquote");
  message.textContent = capsule.note;
  const song = document.createElement("a");
  song.href = capsule.listen_url;
  song.target = "_blank";
  song.rel = "noopener noreferrer";
  const title = capsule.title || capsule.song;
  const showArtist = capsule.artist && !title.toLowerCase().includes(capsule.artist.toLowerCase());
  song.textContent = `♪ ${title}${showArtist ? ` — ${capsule.artist}` : ""} ↗`;
  const meta = document.createElement("p");
  meta.className = "note-meta";
  meta.textContent = [capsule.site && `on ${capsule.site}`, `— ${capsule.author}`].filter(Boolean).join(" · ");
  const screen = document.createElement("div");
  screen.className = "screen";
  screen.append(head, message, song, meta);
  const controls = document.createElement("div");
  controls.className = "tv-controls";
  controls.append(document.createElement("i"), document.createElement("span"));
  const tvCase = document.createElement("div");
  tvCase.className = "tv-case";
  tvCase.append(screen, controls);
  article.append(tvCase);
  return article;
}
let oldestOnWall = null;
async function loadOlderNotes() {
  const response = await fetch(`/api/wall?limit=20&before=${oldestOnWall}`).catch(() => null);
  const capsules = response && response.ok ? await response.json() : [];
  capsules.forEach((capsule) => $("wall-notes").append(makeWallNote(capsule)));
  if (capsules.length) oldestOnWall = capsules[capsules.length - 1].id;
  $("wall-more").classList.toggle("hidden", capsules.length < 20);
}
$("wall-more").addEventListener("click", loadOlderNotes);
async function loadWall() {
  const container = $("wall-notes");
  container.replaceChildren();
  try {
    const response = await fetch("/api/wall?limit=20");
    if (!response.ok) throw new Error();
    const capsules = await response.json();
    if (!capsules.length) {
      const empty = document.createElement("p");
      empty.className = "wall-empty";
      empty.textContent = "The wall is quiet. Your note can be the first.";
      container.append(empty);
      return;
    }
    capsules.forEach((capsule) => container.append(makeWallNote(capsule)));
    oldestOnWall = capsules[capsules.length - 1].id;
    $("wall-more").classList.toggle("hidden", capsules.length < 20);
  } catch {
    const error = document.createElement("p");
    error.className = "wall-empty";
    error.textContent = "The archive is off-air for a moment.";
    container.append(error);
  }
}
shareForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!shareForm.reportValidity()) return;
  const button = event.submitter;
  const body = Object.fromEntries(new FormData(shareForm));
  button.disabled = true;
  button.textContent = "TRANSMITTING…";
  try {
    const response = await fetch("/api/capsules", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : data.detail?.[0]?.msg?.replace(/^Value error, /, "");
      throw new Error(detail || "That transmission couldn't be recorded.");
    }
    await loadWall();
    loadTicker();
    $("wall-status").textContent = data.support ? `${data.message} ${data.support}` : (data.message || "Your note is now part of the signal.");
    $("wall-status").classList.toggle("is-support", Boolean(data.support));
    shareForm.classList.add("hidden");
    $("cassette-heading").classList.add("hidden");
    $("community-wall").classList.remove("hidden");
    $("community-wall").scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "center" });
    shareForm.reset();
    setCassetteSide("front");
  } catch (error) {
    $("share-status").textContent = error.message;
    setCassetteSide("front");
  } finally {
    button.disabled = false;
    button.textContent = "PUT IT ON THE WALL ●";
  }
});
$("share-another").addEventListener("click", () => {
  $("community-wall").classList.add("hidden");
  $("cassette-heading").classList.remove("hidden");
  shareForm.classList.remove("hidden");
  setCassetteSide("front");
  shareForm.elements.url.focus();
});
