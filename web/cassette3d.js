// The share form as a 3D cassette: it floats and turns, you can spin it, and clicking it brings it
// close so you write straight onto its label. Flipping the tape turns it to side B. If WebGL is
// missing, nothing here runs and the flat cassette form stays as it is.
import * as THREE from "/vendor/three.module.min.js";

const stage = document.getElementById("tape-stage");
const canvas = stage?.querySelector("canvas");
const form = document.getElementById("share");
const flipper = document.getElementById("cassette-flipper");
const colorInput = form?.elements.color;
if (!stage || !canvas || !form) throw new Error("no cassette stage");

const COLORS = {
  smoke: { hex: 0x2c3138, opacity: 0.62 }, clear: { hex: 0xdfe6ee, opacity: 0.38 },
  black: { hex: 0x121316, opacity: 0.94 }, mint: { hex: 0x7fd8b4, opacity: 0.78 },
  lilac: { hex: 0xb4a0ea, opacity: 0.78 }, sky: { hex: 0x84c4f2, opacity: 0.78 },
  amber: { hex: 0xf0ae4a, opacity: 0.8 }, rose: { hex: 0xf09cb4, opacity: 0.8 },
};
const W = 10, H = 6.3, D = 1.1;                  // cassette proportions, roughly 100 x 63 x 11 mm
const LABEL_W = 8.6, LABEL_H = 4.4, LABEL_Y = 0.55;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const phone = matchMedia("(max-width: 600px)");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
camera.position.set(0, 0, 15);

scene.add(new THREE.HemisphereLight(0xd6e0ff, 0x0b0b0d, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(-6, 7, 9); scene.add(key);
const rim = new THREE.DirectionalLight(0x7fb2ff, 1.6); rim.position.set(7, -2, -8); scene.add(rim);
const fill = new THREE.PointLight(0xc9d6ff, 18, 30); fill.position.set(4, 3, 7); scene.add(fill);

const tape = new THREE.Group();
scene.add(tape);

function roundedRect(w, h, r) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2 + r, -h / 2); s.lineTo(w / 2 - r, -h / 2); s.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
  s.lineTo(w / 2, h / 2 - r); s.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); s.lineTo(-w / 2 + r, h / 2);
  s.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); s.lineTo(-w / 2, -h / 2 + r); s.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
  return s;
}

// Shell: translucent plastic you can see the reels through.
const shellMaterial = new THREE.MeshPhysicalMaterial({ roughness: 0.32, metalness: 0, clearcoat: 0.9, clearcoatRoughness: 0.2,
  transparent: true, side: THREE.DoubleSide, depthWrite: false });
const shellGeometry = new THREE.ExtrudeGeometry(roundedRect(W, H, 0.38), { depth: D, bevelEnabled: true, bevelSize: 0.08, bevelThickness: 0.08, bevelSegments: 3, curveSegments: 10 });
shellGeometry.translate(0, 0, -D / 2);
const shell = new THREE.Mesh(shellGeometry, shellMaterial);
shell.renderOrder = 2;
tape.add(shell);

// The tab along the bottom edge where the tape is exposed.
const tab = new THREE.Shape();
tab.moveTo(-3.6, -H / 2); tab.lineTo(3.6, -H / 2); tab.lineTo(2.9, -H / 2 + 1.25); tab.lineTo(-2.9, -H / 2 + 1.25); tab.lineTo(-3.6, -H / 2);
const tabGeometry = new THREE.ExtrudeGeometry(tab, { depth: D + 0.3, bevelEnabled: false });
tabGeometry.translate(0, 0, -(D + 0.3) / 2);
const tabMesh = new THREE.Mesh(tabGeometry, shellMaterial);
tabMesh.renderOrder = 2;
tape.add(tabMesh);

// Reels: a wound tape pack and a white hub with teeth on each side.
const packMaterial = new THREE.MeshStandardMaterial({ color: 0x2a1c16, roughness: 0.55, metalness: 0.15 });
const hubMaterial = new THREE.MeshStandardMaterial({ color: 0xece6da, roughness: 0.6 });
const darkMaterial = new THREE.MeshStandardMaterial({ color: 0x0c0c0e, roughness: 0.8 });
const reels = [];
for (const [x, radius] of [[-2.15, 1.55], [2.15, 1.05]]) {
  const reel = new THREE.Group();
  const pack = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 0.42, 48), packMaterial);
  pack.rotation.x = Math.PI / 2;
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.58, 0.5, 32), hubMaterial);
  hub.rotation.x = Math.PI / 2;
  const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.52, 24), darkMaterial);
  hole.rotation.x = Math.PI / 2;
  reel.add(pack, hub, hole);
  for (let i = 0; i < 6; i++) {
    const tooth = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.16, 0.5), hubMaterial);
    const angle = (i / 6) * Math.PI * 2;
    tooth.position.set(Math.cos(angle) * 0.3, Math.sin(angle) * 0.3, 0);
    tooth.rotation.z = angle;
    reel.add(tooth);
  }
  reel.position.set(x, LABEL_Y, 0);
  tape.add(reel);
  reels.push(reel);
}

// Screws at the corners and bottom centre, on both faces.
const screwMaterial = new THREE.MeshStandardMaterial({ color: 0x9aa1aa, roughness: 0.35, metalness: 0.9 });
for (const z of [D / 2 + 0.09, -D / 2 - 0.09]) {
  for (const [x, y] of [[-4.55, 2.8], [4.55, 2.8], [-4.55, -2.8], [4.55, -2.8], [0, -2.55]]) {
    const screw = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.05, 20), screwMaterial);
    screw.rotation.x = Math.PI / 2;
    screw.position.set(x, y, z);
    tape.add(screw);
  }
}

// Paper labels drawn on a canvas, with a window cut out so the reels show through.
// The label text uses the page's web fonts, so wait for them (briefly) before drawing.
await Promise.race([
  Promise.all(["600 58px Caveat", "64px VT323", "30px 'IBM Plex Mono'"].map((font) => document.fonts.load(font))),
  new Promise((resolve) => setTimeout(resolve, 2500)),
]);
function labelTexture(side) {
  const c = document.createElement("canvas");
  c.width = 1024; c.height = Math.round(1024 * LABEL_H / LABEL_W);
  const g = c.getContext("2d");
  g.fillStyle = "#ebe4d3"; g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = "rgba(90,70,40,.08)";
  for (let i = 0; i < 900; i++) g.fillRect(Math.random() * c.width, Math.random() * c.height, 2, 2);
  g.fillStyle = "#1b1d22"; g.fillRect(0, c.height - 70, c.width, 22);
  g.font = "600 58px 'Caveat', cursive"; g.fillStyle = "#24262b";
  g.fillText(side === "A" ? "a song for you" : "what it holds", 60, 92);
  g.font = "700 64px 'VT323', monospace"; g.fillText(side, c.width - 92, 96);
  g.font = "400 30px 'IBM Plex Mono', monospace"; g.fillStyle = "#3d4048";
  g.fillText("MOODiFY · COMMUNITY RECORDING", 60, c.height - 92);
  // the window over the reels
  const wx = c.width * 0.17, wy = c.height * 0.36, ww = c.width * 0.66, wh = c.height * 0.36;
  g.globalCompositeOperation = "destination-out";
  g.beginPath(); g.roundRect(wx, wy, ww, wh, 26); g.fill();
  g.globalCompositeOperation = "source-over";
  g.strokeStyle = "#1b1d22"; g.lineWidth = 6; g.beginPath(); g.roundRect(wx, wy, ww, wh, 26); g.stroke();
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}
const labels = {};
for (const side of ["A", "B"]) {
  const label = new THREE.Mesh(new THREE.PlaneGeometry(LABEL_W, LABEL_H),
    new THREE.MeshStandardMaterial({ map: labelTexture(side), transparent: true, roughness: 0.85 }));
  label.position.set(0, LABEL_Y, side === "A" ? D / 2 + 0.1 : -D / 2 - 0.1);
  if (side === "B") label.rotation.y = Math.PI;
  label.renderOrder = 3;
  tape.add(label);
  labels[side] = label;
}

function setColor(name) {
  const choice = COLORS[name] || COLORS.smoke;
  shellMaterial.color.setHex(choice.hex);
  shellMaterial.opacity = choice.opacity;
  if (colorInput) colorInput.value = name;
  stage.querySelectorAll("[data-color]").forEach((swatch) => swatch.setAttribute("aria-checked", String(swatch.dataset.color === name)));
}
stage.querySelectorAll("[data-color]").forEach((swatch) => swatch.addEventListener("click", () => setColor(swatch.dataset.color)));
setColor(colorInput?.value || "smoke");

// ----- state: idle (floating) or open (close up, writing on the label) -----
let state = "idle";
let yaw = -0.5, pitch = 0.18, targetYaw = yaw, targetPitch = pitch;
let camZ = 15, targetCamZ = 15;
let dragging = false, moved = 0, lastX = 0, lastY = 0, spin = 0;
const side = () => (flipper.classList.contains("is-flipped") ? "B" : "A");

function fitDistance() {
  const aspect = canvas.clientWidth / Math.max(canvas.clientHeight, 1);
  const t = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  // Keep the whole cassette in view, so it still reads as a tape while you write on it.
  const byWidth = (W + 0.8) / (0.94 * 2 * t * aspect);
  const byHeight = (H + 0.8) / (0.9 * 2 * t);
  return Math.max(byWidth, byHeight) + D / 2;
}

function open() {
  if (state === "open") return;
  state = "open";
  stage.dataset.state = "open";
  const facing = side() === "A" ? 0 : Math.PI;
  targetYaw = facing + Math.round((yaw - facing) / (Math.PI * 2)) * Math.PI * 2;
  targetPitch = 0;
  targetCamZ = phone.matches ? 13 : fitDistance();
  form.inert = false;
  setTimeout(() => form.querySelector(side() === "A" ? "[name=url]" : "[name=message]")?.focus({ preventScroll: true }), reduced ? 0 : 700);
}
function close() {
  state = "idle";
  stage.dataset.state = "idle";
  targetCamZ = 15;
  targetPitch = 0.18;
  form.inert = !phone.matches;
}
stage.querySelector(".tape-close")?.addEventListener("click", close);

// Flipping the tape (from the form's own buttons) turns the cassette to the other side.
new MutationObserver(() => {
  if (state !== "open") return;
  targetYaw = (side() === "A" ? 0 : Math.PI) + Math.round((targetYaw - (side() === "A" ? 0 : Math.PI)) / (Math.PI * 2)) * Math.PI * 2;
  stage.classList.add("is-turning");
  setTimeout(() => stage.classList.remove("is-turning"), reduced ? 0 : 650);
}).observe(flipper, { attributes: true, attributeFilter: ["class"] });

canvas.addEventListener("pointerdown", (event) => {
  dragging = true; moved = 0; lastX = event.clientX; lastY = event.clientY;
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", (event) => {
  if (!dragging || state === "open") return;
  const dx = event.clientX - lastX, dy = event.clientY - lastY;
  moved += Math.abs(dx) + Math.abs(dy);
  lastX = event.clientX; lastY = event.clientY;
  targetYaw += dx * 0.012; spin = dx * 0.012;
  targetPitch = THREE.MathUtils.clamp(targetPitch + dy * 0.008, -0.7, 0.7);
});
canvas.addEventListener("pointerup", () => {
  dragging = false;
  if (moved < 6 && state === "idle") open();
});
canvas.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } });
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && state === "open") close(); });

// ----- layout: keep the HTML label pinned over the 3D label while open -----
const corner = new THREE.Vector3();
function placeLabel() {
  if (state !== "open" || phone.matches) return;
  const label = labels[side()];
  label.updateWorldMatrix(true, false);
  const rect = canvas.getBoundingClientRect();
  const xs = [], ys = [];
  for (const [x, y] of [[-LABEL_W / 2, -LABEL_H / 2], [LABEL_W / 2, -LABEL_H / 2], [LABEL_W / 2, LABEL_H / 2], [-LABEL_W / 2, LABEL_H / 2]]) {
    corner.set(x, y, 0).applyMatrix4(label.matrixWorld).project(camera);
    xs.push((corner.x + 1) / 2 * rect.width);
    ys.push((1 - corner.y) / 2 * rect.height);
  }
  const left = Math.min(...xs), top = Math.min(...ys);
  form.style.left = `${left}px`; form.style.top = `${top}px`;
  form.style.width = `${Math.max(...xs) - left}px`; form.style.height = `${Math.max(...ys) - top}px`;
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * renderer.getPixelRatio()) || canvas.height !== Math.round(h * renderer.getPixelRatio())) {
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
    if (state === "open" && !phone.matches) targetCamZ = fitDistance();
  }
}

const clock = new THREE.Clock();
let visible = true;
new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; }).observe(stage);
function frame() {
  requestAnimationFrame(frame);
  if (!visible || document.hidden) return;
  resize();
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;
  if (state === "idle" && !dragging && !reduced) {
    spin *= 0.95;
    targetYaw += 0.0035 + spin;
  }
  const ease = reduced ? 1 : 1 - Math.pow(0.0015, dt);
  yaw += (targetYaw - yaw) * ease;
  pitch += (targetPitch - pitch) * ease;
  camZ += (targetCamZ - camZ) * ease;
  tape.rotation.set(pitch, yaw, state === "idle" ? Math.sin(t * 0.7) * 0.05 : 0);
  tape.position.y = state === "idle" && !reduced ? Math.sin(t * 1.1) * 0.18 : 0;
  camera.position.z = camZ;
  reels.forEach((reel, i) => { reel.rotation.z -= dt * (i ? 1.6 : 1.1); });
  renderer.render(scene, camera);
  placeLabel();
  stage.classList.toggle("is-settled", state === "open" && Math.abs(targetCamZ - camZ) < 0.05 && Math.abs(targetYaw - yaw) < 0.02);
}

document.querySelector(".broadcast")?.classList.add("c3d");
const note = document.querySelector(".broadcast-note");
if (note) note.textContent = "Pick a colour. Click the tape and write on its label, then flip it for side B.";
form.inert = !phone.matches;
phone.addEventListener("change", () => { form.inert = state !== "open" && !phone.matches; });
stage.dataset.state = "idle";
frame();
