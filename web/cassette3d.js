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

// Shell tints: glass colour, how deep the tint gets (lower = stronger), and how see-through it is.
const COLORS = {
  smoke: { hex: 0x5a6270, depth: 0.9, transmission: 0.92 }, clear: { hex: 0xf2f6fb, depth: 9, transmission: 1 },
  black: { hex: 0x1a1c20, depth: 0.25, transmission: 0.55 }, mint: { hex: 0x7fd8b4, depth: 1.2, transmission: 0.96 },
  lilac: { hex: 0xb4a0ea, depth: 1.2, transmission: 0.96 }, sky: { hex: 0x84c4f2, depth: 1.2, transmission: 0.96 },
  amber: { hex: 0xf0ae4a, depth: 1.1, transmission: 0.96 }, rose: { hex: 0xf09cb4, depth: 1.2, transmission: 0.96 },
};
const W = 10, H = 6.3, D = 1.1;                  // cassette proportions, roughly 100 x 63 x 11 mm
const LABEL_W = 8.6, LABEL_H = 4.4, LABEL_Y = 0.55;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const phone = matchMedia("(max-width: 600px)");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
camera.position.set(0, 0, 15);

// A small "studio" of glowing panels, baked into reflections, so the glass has something to mirror.
const studio = new THREE.Scene();
studio.background = new THREE.Color(0x04050a);
for (const [w, h, color, power, pos] of [
  [9, 4, 0xffffff, 4, [0, 7, 5]], [3, 9, 0x9cc2ff, 2.6, [-8, 1, 3]], [3, 9, 0xffd6b0, 1.8, [8, 0, 4]],
  [12, 2, 0xffffff, 1.4, [0, -6, 6]], [6, 3, 0x8fa8ff, 1.2, [0, 2, -9]],
]) {
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(power), side: THREE.DoubleSide }));
  panel.position.set(...pos);
  panel.lookAt(0, 0, 0);
  studio.add(panel);
}
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(studio, 0.035).texture;

const key = new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(-6, 7, 9); scene.add(key);
const rim = new THREE.DirectionalLight(0x7fb2ff, 1.2); rim.position.set(7, -2, -8); scene.add(rim);

// A soft contact shadow on an unseen floor, so the tape hovers over something.
const shadowCanvas = document.createElement("canvas");
shadowCanvas.width = shadowCanvas.height = 128;
const sg = shadowCanvas.getContext("2d");
const grad = sg.createRadialGradient(64, 64, 4, 64, 64, 64);
grad.addColorStop(0, "rgba(0,0,0,.65)"); grad.addColorStop(1, "rgba(0,0,0,0)");
sg.fillStyle = grad; sg.fillRect(0, 0, 128, 128);
const shadow = new THREE.Mesh(new THREE.PlaneGeometry(12, 4),
  new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(shadowCanvas), transparent: true, depthWrite: false }));
shadow.rotation.x = -Math.PI / 2;
shadow.position.y = -H / 2 - 1.3;
scene.add(shadow);

const tape = new THREE.Group();
scene.add(tape);

function roundedRect(w, h, r) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2 + r, -h / 2); s.lineTo(w / 2 - r, -h / 2); s.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
  s.lineTo(w / 2, h / 2 - r); s.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); s.lineTo(-w / 2 + r, h / 2);
  s.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); s.lineTo(-w / 2, -h / 2 + r); s.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
  return s;
}

// Shell: glass-clear moulded plastic. Transmission refracts the reels and tape inside it, clearcoat
// adds the hard polished shine, and the studio panels give it reflections.
const shellMaterial = new THREE.MeshPhysicalMaterial({ roughness: 0.05, metalness: 0, transmission: 1, thickness: 0.55, ior: 1.49,
  clearcoat: 1, clearcoatRoughness: 0.03, specularIntensity: 1, envMapIntensity: 1.35, dispersion: 0.25 });
const shellGeometry = new THREE.ExtrudeGeometry(roundedRect(W, H, 0.38), { depth: D, bevelEnabled: true, bevelSize: 0.08, bevelThickness: 0.08, bevelSegments: 3, curveSegments: 10 });
shellGeometry.translate(0, 0, -D / 2);
const shell = new THREE.Mesh(shellGeometry, shellMaterial);
tape.add(shell);

// The tab along the bottom edge where the tape is exposed.
const tab = new THREE.Shape();
tab.moveTo(-3.6, -H / 2); tab.lineTo(3.6, -H / 2); tab.lineTo(2.9, -H / 2 + 1.25); tab.lineTo(-2.9, -H / 2 + 1.25); tab.lineTo(-3.6, -H / 2);
const tabGeometry = new THREE.ExtrudeGeometry(tab, { depth: D + 0.3, bevelEnabled: false });
tabGeometry.translate(0, 0, -(D + 0.3) / 2);
const tabMesh = new THREE.Mesh(tabGeometry, shellMaterial);
tape.add(tabMesh);

// Reels: a wound tape pack and a white hub with teeth on each side.
const packMaterial = new THREE.MeshStandardMaterial({ color: 0x3a2418, roughness: 0.32, metalness: 0.45 });
const hubMaterial = new THREE.MeshStandardMaterial({ color: 0xece6da, roughness: 0.6 });
const darkMaterial = new THREE.MeshStandardMaterial({ color: 0x0c0c0e, roughness: 0.8 });
const reels = [];
for (const [x, radius] of [[-2.15, 1.55], [2.15, 1.05]]) {
  const reel = new THREE.Group();
  const pack = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 0.42, 48), packMaterial);
  pack.rotation.x = Math.PI / 2;
  // translucent flanges either side of the pack, a white hub ring with six spokes and teeth
  const flange = new THREE.MeshPhysicalMaterial({ color: 0xe8edf2, roughness: 0.15, transmission: 0.85, thickness: 0.05, transparent: true });
  for (const z of [-0.24, 0.24]) {
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(1.7, 1.7, 0.03, 64), flange);
    disc.rotation.x = Math.PI / 2;
    disc.position.z = z;
    reel.add(disc);
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.09, 12, 40), hubMaterial);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.5, 32), hubMaterial);
  hub.rotation.x = Math.PI / 2;
  const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.52, 24), darkMaterial);
  hole.rotation.x = Math.PI / 2;
  reel.add(pack, ring, hub, hole);
  for (let i = 0; i < 6; i++) {
    const angle = (i / 6) * Math.PI * 2;
    const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.1, 0.3), hubMaterial);
    spoke.position.set(Math.cos(angle) * 0.47, Math.sin(angle) * 0.47, 0);
    spoke.rotation.z = angle;
    const tooth = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.14, 0.5), hubMaterial);
    tooth.position.set(Math.cos(angle + 0.5) * 0.22, Math.sin(angle + 0.5) * 0.22, 0);
    tooth.rotation.z = angle + 0.5;
    reel.add(spoke, tooth);
  }
  reel.position.set(x, LABEL_Y, 0);
  reel.userData.pack = pack;
  reel.userData.radius = radius;
  tape.add(reel);
  reels.push(reel);
}

// Inside the shell: the tape ribbon running from reel to reel past the guides and the felt pad.
const ribbonMaterial = new THREE.MeshStandardMaterial({ color: 0x3b2417, roughness: 0.3, metalness: 0.5 });
const path = new THREE.CatmullRomCurve3([
  [-3.55, -0.2], [-4.0, -1.7], [-3.75, -2.35], [-2.6, -2.62], [2.6, -2.62], [3.75, -2.35], [4.0, -1.7], [3.1, 0.15],
].map(([x, y]) => new THREE.Vector3(x, y, 0)));
tape.add(new THREE.Mesh(new THREE.TubeGeometry(path, 120, 0.04, 6), ribbonMaterial));
const whitePlastic = new THREE.MeshStandardMaterial({ color: 0xf1ede4, roughness: 0.4 });
const steel = new THREE.MeshStandardMaterial({ color: 0xc4cad2, roughness: 0.22, metalness: 1 });
for (const [x, y, radius, material] of [[-3.75, -2.35, 0.2, whitePlastic], [3.75, -2.35, 0.2, whitePlastic],
  [-2.6, -2.62, 0.09, steel], [2.6, -2.62, 0.09, steel]]) {
  const guide = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 0.6, 24), material);
  guide.rotation.x = Math.PI / 2;
  guide.position.set(x, y, 0);
  tape.add(guide);
}
const felt = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.16, 0.34), new THREE.MeshStandardMaterial({ color: 0x4a3f36, roughness: 1 }));
felt.position.set(0, -2.74, 0);
const spring = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.05, 0.3), steel);
spring.position.set(0, -2.6, 0);
tape.add(felt, spring);
const postMaterial = new THREE.MeshStandardMaterial({ color: 0x15171b, roughness: 0.5, transparent: true, opacity: 0.55 });
for (const [x, y] of [[-4.55, 2.8], [4.55, 2.8], [-4.55, -2.8], [4.55, -2.8], [0, -2.55]]) {
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, D * 0.92, 20), postMaterial);
  post.rotation.x = Math.PI / 2;
  post.position.set(x, y, 0);
  tape.add(post);
}

// Moulded details: grip ribs down both short edges and the write-protect tabs on the top edge.
const rib = new THREE.MeshStandardMaterial({ color: 0x0f1013, roughness: 0.45, transparent: true, opacity: 0.55 });
for (const z of [D / 2 + 0.06, -D / 2 - 0.06]) {
  for (const sx of [-1, 1]) {
    for (let i = 0; i < 6; i++) {
      const line = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.05, 0.02), rib);
      line.position.set(sx * 4.72, -1.3 + i * 0.28, z);
      tape.add(line);
    }
  }
}
for (const x of [-3.9, 3.9]) {
  const notch = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.22, D * 0.7), darkMaterial);
  notch.position.set(x, H / 2 - 0.08, 0);
  tape.add(notch);
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
function wrap(g, text, x, y, width, lineHeight, maxLines) {
  const words = text.split(/\s+/).filter(Boolean);
  let line = "", lines = 0;
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (g.measureText(test).width > width && line) {
      g.fillText(lines === maxLines - 1 ? `${line}…` : line, x, y + lines * lineHeight);
      if (++lines >= maxLines) return;
      line = word;
    } else line = test;
  }
  if (line) g.fillText(line, x, y + lines * lineHeight);
}
const ink = { A: "", B: "", name: "" };
function labelTexture(side, existing) {
  const c = existing?.image || document.createElement("canvas");
  c.width = 1024; c.height = Math.round(1024 * LABEL_H / LABEL_W);
  const g = c.getContext("2d");
  g.fillStyle = "#ebe4d3"; g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = "rgba(90,70,40,.08)";
  for (let i = 0; i < 900; i++) g.fillRect(Math.random() * c.width, Math.random() * c.height, 2, 2);
  g.strokeStyle = "rgba(40,44,52,.18)"; g.lineWidth = 2;
  for (let y = 132; y < c.height * 0.34; y += 30) { g.beginPath(); g.moveTo(60, y); g.lineTo(c.width - 60, y); g.stroke(); }
  [["#c9533f", 12], ["#e4a43b", 12], ["#2f6f8f", 12]].forEach(([color, h], i) => { g.fillStyle = color; g.fillRect(0, c.height - 128 + i * 15, c.width, h); });
  g.fillStyle = "#1b1d22"; g.fillRect(0, c.height - 70, c.width, 22);
  g.font = "600 58px 'Caveat', cursive"; g.fillStyle = "#24262b";
  if (side === "A") {
    g.fillText(ink.A ? ink.A.replace(/^https?:\/\/(www\.)?/, "").slice(0, 34) : "a song for you", 60, 92);
  } else if (ink.B) {
    g.font = "600 40px 'Caveat', cursive";
    wrap(g, ink.B, 60, 78, c.width - 200, 30, 2);
  } else g.fillText("what it holds", 60, 92);
  if (side === "B" && ink.name) { g.font = "600 40px 'Caveat', cursive"; g.fillStyle = "#2f6f8f"; g.fillText(`— ${ink.name}`.slice(0, 30), c.width - 420, c.height * 0.33); g.fillStyle = "#24262b"; }
  g.font = "700 64px 'VT323', monospace"; g.fillText(side, c.width - 92, 96);
  g.font = "400 30px 'IBM Plex Mono', monospace"; g.fillStyle = "#3d4048";
  g.fillText("MOODiFY · COMMUNITY RECORDING", 60, c.height - 92);
  // the window over the reels
  const wx = c.width * 0.17, wy = c.height * 0.36, ww = c.width * 0.66, wh = c.height * 0.36;
  g.globalCompositeOperation = "destination-out";
  g.beginPath(); g.roundRect(wx, wy, ww, wh, 26); g.fill();
  g.globalCompositeOperation = "source-over";
  g.strokeStyle = "#1b1d22"; g.lineWidth = 6; g.beginPath(); g.roundRect(wx, wy, ww, wh, 26); g.stroke();
  if (existing) { existing.needsUpdate = true; return existing; }
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}
const labels = {};
for (const side of ["A", "B"]) {
  const label = new THREE.Mesh(new THREE.PlaneGeometry(LABEL_W, LABEL_H),
    new THREE.MeshStandardMaterial({ map: labelTexture(side), transparent: true, alphaTest: 0.5, roughness: 0.85 }));
  label.position.set(0, LABEL_Y, side === "A" ? D / 2 + 0.1 : -D / 2 - 0.1);
  if (side === "B") label.rotation.y = Math.PI;
  tape.add(label);
  labels[side] = label;
}
// Whatever you type is handwritten onto the label as you go.
form.addEventListener("input", () => {
  ink.A = form.elements.url.value.trim();
  ink.B = form.elements.message.value.trim();
  ink.name = form.elements.name.value.trim();
  for (const side of ["A", "B"]) labelTexture(side, labels[side].material.map);
  // the take-up reel fills as the message grows
  const share = Math.min(ink.B.length / 400, 1);
  reels[0].userData.pack.scale.set(1 - share * 0.3, 1, 1 - share * 0.3);
  reels[1].userData.pack.scale.set(1 + share * 0.45, 1, 1 + share * 0.45);
});
form.addEventListener("reset", () => setTimeout(() => form.dispatchEvent(new Event("input")), 0));

function setColor(name) {
  const choice = COLORS[name] || COLORS.smoke;
  shellMaterial.color.setHex(choice.hex);
  shellMaterial.attenuationColor.setHex(choice.hex);
  shellMaterial.attenuationDistance = choice.depth;
  shellMaterial.transmission = choice.transmission;
  if (colorInput) colorInput.value = name;
  stage.querySelectorAll("[data-color]").forEach((swatch) => swatch.setAttribute("aria-checked", String(swatch.dataset.color === name)));
}
stage.querySelectorAll("[data-color]").forEach((swatch) => swatch.addEventListener("click", () => setColor(swatch.dataset.color)));
setColor(colorInput?.value || "smoke");

// ----- state: idle (floating) or open (close up, writing on the label) -----
let state = "idle";
let yaw = -0.5, pitch = 0.18, targetYaw = yaw, targetPitch = pitch;
let camZ = 15, targetCamZ = 15;

// Far enough that the whole tape fits at any angle you can turn it to, on any screen shape.
function idleDistance() {
  const aspect = canvas.clientWidth / Math.max(canvas.clientHeight, 1);
  const t = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  return Math.max(12.6 / (2 * t * aspect), 9 / (2 * t)) + D;
}
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
  targetCamZ = phone.matches ? idleDistance() * 0.85 : fitDistance();
  form.inert = false;
  setTimeout(() => form.querySelector(side() === "A" ? "[name=url]" : "[name=message]")?.focus({ preventScroll: true }), reduced ? 0 : 700);
}
function close() {
  state = "idle";
  stage.dataset.state = "idle";
  targetCamZ = idleDistance();
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
    if (state === "idle") targetCamZ = idleDistance();
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
  shadow.material.opacity += ((state === "idle" ? 1 : 0) - shadow.material.opacity) * ease;
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
