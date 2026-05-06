const canvas = document.querySelector("#contract-scene");
const statusPill = document.querySelector("#status-pill");
const clauseCount = document.querySelector("#clause-count");
const riskScore = document.querySelector("#risk-score");
const riskLevel = document.querySelector("#risk-level");
const missingCount = document.querySelector("#missing-count");
const summaryText = document.querySelector("#summary-text");
const clauseList = document.querySelector("#clause-list");
const fileInput = document.querySelector("#contract-file");
const fileName = document.querySelector("#file-name");
const contractText = document.querySelector("#contract-text");
const contractType = document.querySelector("#contract-type");
const analysisDepth = document.querySelector("#analysis-depth");
const jurisdiction = document.querySelector("#jurisdiction");
const analyzeButton = document.querySelector("#analyze-button");
const sampleButton = document.querySelector("#sample-button");

const sampleContract = `MUTUAL NON-DISCLOSURE AGREEMENT

Confidentiality
Each party shall protect the other party's confidential information using reasonable care and must not disclose it to third parties except to employees and contractors with a need to know.

Term and Termination
Either party may terminate this Agreement with thirty days written notice. Confidentiality obligations survive for three years after termination.

Governing Law
This Agreement is governed by the laws of New York.

Limitation of Liability
Vendor's liability is uncapped for all claims and damages arising out of this Agreement.

Automatic Renewal
This Agreement will automatically renew for successive one year terms unless either party gives notice at least five days before renewal.`;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x07100f, 18, 50);

const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 8, 18);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
if ("outputColorSpace" in renderer && THREE.SRGBColorSpace) {
  renderer.outputColorSpace = THREE.SRGBColorSpace;
} else {
  renderer.outputEncoding = THREE.sRGBEncoding;
}

const cameraRig = {
  radius: 18,
  theta: 0,
  phi: 1.1,
  target: new THREE.Vector3(0, 1.6, 0),
  targetGoal: new THREE.Vector3(0, 1.6, 0),
};

function updateCamera() {
  cameraRig.phi = Math.min(1.36, Math.max(0.42, cameraRig.phi));
  cameraRig.radius = Math.min(32, Math.max(8, cameraRig.radius));
  cameraRig.target.lerp(cameraRig.targetGoal, 0.08);
  camera.position.set(
    cameraRig.target.x + Math.sin(cameraRig.theta) * Math.sin(cameraRig.phi) * cameraRig.radius,
    cameraRig.target.y + Math.cos(cameraRig.phi) * cameraRig.radius,
    cameraRig.target.z + Math.cos(cameraRig.theta) * Math.sin(cameraRig.phi) * cameraRig.radius
  );
  camera.lookAt(cameraRig.target);
}

scene.add(new THREE.HemisphereLight(0xdffcf3, 0x0f1a18, 1.8));

const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
keyLight.position.set(-8, 12, 8);
scene.add(keyLight);

const accentLight = new THREE.PointLight(0x37d6bd, 7, 24);
accentLight.position.set(7, 5, 7);
scene.add(accentLight);

const floor = new THREE.Mesh(
  new THREE.CylinderGeometry(10.5, 12.8, 0.3, 96),
  new THREE.MeshStandardMaterial({ color: 0x13211f, roughness: 0.72, metalness: 0.1 })
);
floor.position.y = -0.18;
scene.add(floor);

const grid = new THREE.GridHelper(24, 24, 0x37d6bd, 0x244641);
grid.position.y = 0.02;
grid.material.opacity = 0.28;
grid.material.transparent = true;
scene.add(grid);

const nodeGroup = new THREE.Group();
scene.add(nodeGroup);

const rings = [];
for (let i = 0; i < 3; i += 1) {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(3.8 + i * 2.2, 0.015, 8, 128),
    new THREE.MeshBasicMaterial({ color: i === 1 ? 0xd8f46a : 0x37d6bd, transparent: true, opacity: 0.35 - i * 0.06 })
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.08 + i * 0.02;
  rings.push(ring);
  scene.add(ring);
}

let clauseMeshes = [];
let selectedClauseId = null;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function riskColor(score) {
  if (score >= 6) return 0xff6d6d;
  if (score >= 3) return 0xffbf61;
  return 0x37d6bd;
}

function riskClass(score) {
  if (score >= 6) return "high";
  if (score >= 3) return "medium";
  return "low";
}

function resetScene() {
  for (const mesh of clauseMeshes) {
    nodeGroup.remove(mesh);
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
  clauseMeshes = [];
}

function populateScene(clauses) {
  resetScene();
  const count = Math.max(clauses.length, 1);
  clauses.forEach((clause, index) => {
    const score = Number(clause.risk_score || 0);
    const angle = (index / count) * Math.PI * 2;
    const radius = 4.2 + (index % 3) * 1.4;
    const height = 0.75 + score * 0.32;
    const geometry = new THREE.BoxGeometry(0.95, height, 0.95);
    const material = new THREE.MeshStandardMaterial({
      color: riskColor(score),
      emissive: riskColor(score),
      emissiveIntensity: 0.12,
      roughness: 0.38,
      metalness: 0.35,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(Math.cos(angle) * radius, height / 2, Math.sin(angle) * radius);
    mesh.rotation.y = -angle;
    mesh.userData = { clause, baseY: height / 2, angle };
    clauseMeshes.push(mesh);
    nodeGroup.add(mesh);
  });
}

function setStatus(text) {
  statusPill.textContent = text;
}

function formatType(type) {
  return String(type || "clause").replaceAll("_", " ");
}

function renderReport(report) {
  const clauses = report.clauses || [];
  const summary = report.risk_summary || {};
  const executive = report.executive_summary || {};

  clauseCount.textContent = `${clauses.length} clauses`;
  riskScore.textContent = `${Number(summary.overall_risk_score || 0).toFixed(1)} risk`;
  riskLevel.textContent = summary.risk_level || "None";
  missingCount.textContent = String((summary.missing_clauses || []).length);
  summaryText.textContent = executive.one_paragraph || "No summary returned.";

  clauseList.replaceChildren();
  for (const clause of clauses) {
    const button = document.createElement("button");
    button.className = "clause-card";
    button.type = "button";
    button.dataset.clauseId = clause.clause_id;
    button.innerHTML = `
      <header>
        <h2>${clause.clause_id} · ${formatType(clause.clause_type)}</h2>
        <span class="score ${riskClass(clause.risk_score)}">${Number(clause.risk_score || 0).toFixed(1)}</span>
      </header>
      <p>${clause.plain_english || clause.verbatim_text || ""}</p>
    `;
    button.addEventListener("click", () => selectClause(clause.clause_id));
    clauseList.append(button);
  }

  selectedClauseId = clauses[0]?.clause_id || null;
  populateScene(clauses);
  syncSelection();
}

function syncSelection() {
  document.querySelectorAll(".clause-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.clauseId === selectedClauseId);
  });
  for (const mesh of clauseMeshes) {
    const active = mesh.userData.clause.clause_id === selectedClauseId;
    mesh.scale.set(active ? 1.22 : 1, active ? 1.1 : 1, active ? 1.22 : 1);
    mesh.material.emissiveIntensity = active ? 0.45 : 0.12;
  }
}

function selectClause(clauseId) {
  selectedClauseId = clauseId;
  syncSelection();
  const mesh = clauseMeshes.find((item) => item.userData.clause.clause_id === clauseId);
  if (mesh) {
    cameraRig.targetGoal.set(mesh.position.x, mesh.position.y, mesh.position.z);
  }
}

async function analyzeContract() {
  setStatus("Analyzing");
  analyzeButton.disabled = true;
  try {
    const formData = new FormData();
    if (fileInput.files[0]) {
      formData.append("file", fileInput.files[0]);
    } else {
      const text = contractText.value.trim() || sampleContract;
      formData.append("file", new File([text], "pasted-contract.txt", { type: "text/plain" }));
    }
    formData.append("contract_type", contractType.value);
    formData.append("depth", analysisDepth.value);
    formData.append("jurisdiction", jurisdiction.value);

    const response = await fetch("/analyze", { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Analyze failed with ${response.status}`);
    const report = await response.json();
    renderReport(report);
    setStatus("Complete");
  } catch (error) {
    setStatus("Error");
    summaryText.textContent = error.message || "Analysis failed.";
  } finally {
    analyzeButton.disabled = false;
  }
}

function loadSample() {
  fileInput.value = "";
  fileName.textContent = "Pasted sample";
  contractText.value = sampleContract;
  contractType.value = "nda";
  jurisdiction.value = "New York";
}

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "Contract file";
});
sampleButton.addEventListener("click", loadSample);
analyzeButton.addEventListener("click", analyzeContract);

canvas.addEventListener("pointermove", (event) => {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(clauseMeshes)[0];
  canvas.style.cursor = hit ? "pointer" : "grab";
});

let dragging = false;
let lastPointer = { x: 0, y: 0 };

canvas.addEventListener("pointerdown", (event) => {
  dragging = true;
  lastPointer = { x: event.clientX, y: event.clientY };
  canvas.setPointerCapture(event.pointerId);
});

canvas.addEventListener("pointerup", (event) => {
  dragging = false;
  canvas.releasePointerCapture(event.pointerId);
});

canvas.addEventListener("pointerleave", () => {
  dragging = false;
});

canvas.addEventListener("pointermove", (event) => {
  if (!dragging) return;
  const deltaX = event.clientX - lastPointer.x;
  const deltaY = event.clientY - lastPointer.y;
  lastPointer = { x: event.clientX, y: event.clientY };
  cameraRig.theta -= deltaX * 0.006;
  cameraRig.phi -= deltaY * 0.004;
});

canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  cameraRig.radius += Math.sign(event.deltaY) * 1.2;
}, { passive: false });

canvas.addEventListener("pointerdown", (event) => {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(clauseMeshes)[0];
  if (hit) selectClause(hit.object.userData.clause.clause_id);
});

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function animate(time = 0) {
  nodeGroup.rotation.y += 0.0015;
  rings.forEach((ring, index) => {
    ring.rotation.z += 0.001 + index * 0.0008;
  });
  for (const mesh of clauseMeshes) {
    mesh.position.y = mesh.userData.baseY + Math.sin(time * 0.0015 + mesh.userData.angle) * 0.08;
  }
  updateCamera();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

loadSample();
populateScene([
  { clause_id: "C001", clause_type: "confidentiality", risk_score: 2.0, plain_english: "Mutual confidentiality obligations." },
  { clause_id: "C002", clause_type: "termination", risk_score: 2.0, plain_english: "Thirty day termination notice." },
  { clause_id: "C003", clause_type: "liability", risk_score: 6.5, plain_english: "Uncapped liability exposure." },
  { clause_id: "C004", clause_type: "auto_renewal", risk_score: 4.5, plain_english: "Automatic renewal with short notice." },
]);
animate();
