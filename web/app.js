const seen = [];
let lastMode = "relate";
const $ = (id) => document.getElementById(id);

async function findCapsule(mode) {
  const text = $("feeling").value.trim();
  if (text.length < 3) return $("feeling").focus();
  lastMode = mode;
  const response = await fetch("/api/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, mode, seen }),
  });
  if (!response.ok) return;
  const data = await response.json();
  $("result").classList.remove("hidden");
  $("support").textContent = data.support || "";
  $("support").classList.toggle("hidden", !data.support);
  const reading = data.source === "safety" ? "" :
    `Read as ${data.mood} (${data.source === "llm" ? "AI" : "offline reader"})` +
    (data.target_mood !== data.mood ? ` · lifting toward ${data.target_mood}` : "");
  $("reading").textContent = reading;
  const capsule = data.capsule;
  if (!capsule) return;
  seen.push(capsule.id);
  $("song").textContent = capsule.song;
  $("artist").textContent = capsule.artist;
  $("note").textContent = capsule.note;
  $("author").textContent = `Shared by ${capsule.author}`;
}

document.querySelectorAll("[data-mode]").forEach((button) =>
  button.addEventListener("click", () => findCapsule(button.dataset.mode)));
$("another").addEventListener("click", () => findCapsule(lastMode));

fetch("/api/moods").then((r) => r.json()).then((moods) => {
  $("mood-select").innerHTML = '<option value="">Mood</option>' +
    moods.map((m) => `<option value="${m}">${m}</option>`).join("");
});

$("share").addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = Object.fromEntries(new FormData(event.target));
  const response = await fetch("/api/capsules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (response.ok) {
    event.target.reset();
    $("share-status").textContent = "Shared. Someone who feels this way will get it.";
  } else {
    const error = await response.json();
    $("share-status").textContent = error.detail?.[0]?.msg || "Couldn't share that capsule.";
  }
});
