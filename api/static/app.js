const canvas = document.querySelector("#contract-scene");
const statusPill = document.querySelector("#status-pill");
const clauseCount = document.querySelector("#clause-count");
const riskScore = document.querySelector("#risk-score");
const riskLevel = document.querySelector("#risk-level");
const missingCount = document.querySelector("#missing-count");
const summaryText = document.querySelector("#summary-text");
const clauseList = document.querySelector("#clause-list");
const obligationPanel = document.querySelector("#obligation-panel");
const compareSummary = document.querySelector("#compare-summary");
const fileInput = document.querySelector("#contract-file");
const fileName = document.querySelector("#file-name");
const compareFileInput = document.querySelector("#compare-file");
const compareFileName = document.querySelector("#compare-file-name");
const compareInputs = document.querySelector("#compare-inputs");
const contractText = document.querySelector("#contract-text");
const compareText = document.querySelector("#compare-text");
const contractType = document.querySelector("#contract-type");
const analysisDepth = document.querySelector("#analysis-depth");
const jurisdiction = document.querySelector("#jurisdiction");
const analyzeButton = document.querySelector("#analyze-button");
const sampleButton = document.querySelector("#sample-button");
const modeAnalyze = document.querySelector("#mode-analyze");
const modeCompare = document.querySelector("#mode-compare");
const clauseSearch = document.querySelector("#clause-search");
const riskFilter = document.querySelector("#risk-filter");
const exportJson = document.querySelector("#export-json");
const exportMarkdown = document.querySelector("#export-markdown");
const exportHtml = document.querySelector("#export-html");

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

const revisedSampleContract = `${sampleContract}

Data Privacy
Vendor shall comply with GDPR, CCPA, and all applicable data protection laws.`;

const appState = {
  mode: "analyze",
  report: null,
  compare: null,
  selectedClauseId: null,
};

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

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char]
  ));
}

function filteredClauses() {
  const clauses = appState.report?.clauses || [];
  const query = clauseSearch.value.trim().toLowerCase();
  const risk = riskFilter.value;
  return clauses.filter((clause) => {
    const scoreClass = riskClass(clause.risk_score);
    const haystack = [
      clause.clause_id,
      clause.clause_type,
      clause.heading,
      clause.plain_english,
      clause.verbatim_text,
      ...(clause.risk_flags || []),
      ...(clause.obligations || []),
    ].join(" ").toLowerCase();
    return (risk === "all" || risk === scoreClass) && (!query || haystack.includes(query));
  });
}

function renderReport(report) {
  appState.report = report;
  appState.compare = null;
  compareSummary.hidden = true;

  const clauses = report.clauses || [];
  const summary = report.risk_summary || {};
  const executive = report.executive_summary || {};

  clauseCount.textContent = `${clauses.length} clauses`;
  riskScore.textContent = `${Number(summary.overall_risk_score || 0).toFixed(1)} risk`;
  riskLevel.textContent = summary.risk_level || "None";
  missingCount.textContent = String((summary.missing_clauses || []).length);
  summaryText.textContent = executive.one_paragraph || "No summary returned.";

  appState.selectedClauseId = clauses[0]?.clause_id || null;
  populateScene(clauses);
  renderClauseList();
  renderObligations();
}

function renderClauseList() {
  const clauses = filteredClauses();
  clauseList.replaceChildren();
  for (const clause of clauses) {
    const button = document.createElement("button");
    button.className = "clause-card";
    button.type = "button";
    button.dataset.clauseId = clause.clause_id;
    button.innerHTML = `
      <header>
        <h2>${escapeHtml(clause.clause_id)} - ${escapeHtml(formatType(clause.clause_type))}</h2>
        <span class="score ${riskClass(clause.risk_score)}">${Number(clause.risk_score || 0).toFixed(1)}</span>
      </header>
      <p>${escapeHtml(clause.plain_english || clause.verbatim_text || "")}</p>
    `;
    button.addEventListener("click", () => selectClause(clause.clause_id));
    clauseList.append(button);
  }
  if (!clauses.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = appState.report ? "No clauses match the current filters." : "Run analysis to see clauses.";
    clauseList.append(empty);
  }
  syncSelection();
}

function renderObligations() {
  const clauses = appState.report?.clauses || [];
  const grouped = new Map();
  for (const clause of clauses) {
    for (const obligation of clause.obligations || []) {
      const key = clause.party_bound || "unspecified";
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push({ clauseId: clause.clause_id, text: obligation });
    }
  }

  obligationPanel.replaceChildren();
  const title = document.createElement("h2");
  title.textContent = "Obligations";
  obligationPanel.append(title);

  if (!grouped.size) {
    const empty = document.createElement("p");
    empty.textContent = "No explicit obligations detected yet.";
    obligationPanel.append(empty);
    return;
  }

  for (const [party, items] of grouped.entries()) {
    const group = document.createElement("section");
    group.innerHTML = `<h3>${escapeHtml(formatType(party))}</h3>`;
    const list = document.createElement("ul");
    for (const item of items.slice(0, 5)) {
      const li = document.createElement("li");
      li.textContent = `${item.clauseId}: ${item.text}`;
      list.append(li);
    }
    group.append(list);
    obligationPanel.append(group);
  }
}

function renderCompare(result) {
  appState.compare = result;
  appState.report = null;
  resetScene();
  clauseList.replaceChildren();
  obligationPanel.replaceChildren();
  compareSummary.hidden = false;

  const added = result.added_clause_types || [];
  const deleted = result.deleted_clause_types || [];
  const changed = result.changed_clauses || [];
  const vectors = result.new_risk_vectors || [];
  const total = added.length + deleted.length + changed.length;

  clauseCount.textContent = `${total} changes`;
  riskScore.textContent = `${vectors.length} new risks`;
  riskLevel.textContent = vectors.length ? "Review" : "Stable";
  missingCount.textContent = String(deleted.length);
  summaryText.textContent = total
    ? "Comparison complete. Review added, deleted, and changed clause types before sending the revised contract."
    : "Comparison complete. No clause-level changes were detected.";

  compareSummary.innerHTML = `
    <div><span>Added</span><strong>${added.length}</strong></div>
    <div><span>Deleted</span><strong>${deleted.length}</strong></div>
    <div><span>Changed</span><strong>${changed.length}</strong></div>
  `;

  const rows = [
    ...added.map((type) => ({ label: "Added", type, score: 4.5 })),
    ...deleted.map((type) => ({ label: "Deleted", type, score: 5.5 })),
    ...changed.map((item) => ({ label: "Changed", type: item.clause_type, score: item.risk_delta > 0 ? 6.5 : 3.5, delta: item.risk_delta })),
  ];

  populateScene(rows.map((row, index) => ({
    clause_id: `D${String(index + 1).padStart(3, "0")}`,
    clause_type: row.type,
    risk_score: row.score,
    plain_english: `${row.label}: ${formatType(row.type)}${row.delta !== undefined ? `, risk delta ${row.delta}` : ""}`,
  })));

  for (const row of rows) {
    const card = document.createElement("button");
    card.className = "clause-card";
    card.type = "button";
    card.innerHTML = `
      <header>
        <h2>${escapeHtml(row.label)} - ${escapeHtml(formatType(row.type))}</h2>
        <span class="score ${riskClass(row.score)}">${row.delta !== undefined ? escapeHtml(row.delta) : row.score.toFixed(1)}</span>
      </header>
      <p>${escapeHtml(row.delta !== undefined ? `Risk delta: ${row.delta}` : "Clause presence changed between versions.")}</p>
    `;
    clauseList.append(card);
  }
}

function syncSelection() {
  document.querySelectorAll(".clause-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.clauseId === appState.selectedClauseId);
  });
  for (const mesh of clauseMeshes) {
    const active = mesh.userData.clause.clause_id === appState.selectedClauseId;
    mesh.scale.set(active ? 1.22 : 1, active ? 1.1 : 1, active ? 1.22 : 1);
    mesh.material.emissiveIntensity = active ? 0.45 : 0.12;
  }
}

function selectClause(clauseId) {
  appState.selectedClauseId = clauseId;
  syncSelection();
  const mesh = clauseMeshes.find((item) => item.userData.clause.clause_id === clauseId);
  if (mesh) {
    cameraRig.targetGoal.set(mesh.position.x, mesh.position.y, mesh.position.z);
  }
}

function textFileFromTextarea(textarea, filename) {
  return new File([textarea.value.trim() || sampleContract], filename, { type: "text/plain" });
}

function appendContractFile(formData, fieldName, fileInputElement, textAreaElement, fallbackName) {
  if (fileInputElement.files[0]) {
    formData.append(fieldName, fileInputElement.files[0]);
  } else {
    formData.append(fieldName, textFileFromTextarea(textAreaElement, fallbackName));
  }
}

async function analyzeContract() {
  setStatus("Analyzing");
  analyzeButton.disabled = true;
  try {
    const formData = new FormData();
    appendContractFile(formData, "file", fileInput, contractText, "pasted-contract.txt");
    formData.append("contract_type", contractType.value);
    formData.append("depth", analysisDepth.value);
    formData.append("jurisdiction", jurisdiction.value);

    const response = await fetch("/analyze", { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Analyze failed with ${response.status}`);
    renderReport(await response.json());
    setStatus("Complete");
  } catch (error) {
    setStatus("Error");
    summaryText.textContent = error.message || "Analysis failed.";
  } finally {
    analyzeButton.disabled = false;
  }
}

async function compareContracts() {
  setStatus("Comparing");
  analyzeButton.disabled = true;
  try {
    const formData = new FormData();
    appendContractFile(formData, "old_file", fileInput, contractText, "original-contract.txt");
    appendContractFile(formData, "new_file", compareFileInput, compareText, "revised-contract.txt");
    formData.append("contract_type", contractType.value);
    formData.append("jurisdiction", jurisdiction.value);

    const response = await fetch("/compare", { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Compare failed with ${response.status}`);
    renderCompare(await response.json());
    setStatus("Complete");
  } catch (error) {
    setStatus("Error");
    summaryText.textContent = error.message || "Comparison failed.";
  } finally {
    analyzeButton.disabled = false;
  }
}

function loadSample() {
  fileInput.value = "";
  compareFileInput.value = "";
  fileName.textContent = "Pasted sample";
  compareFileName.textContent = "Revised sample";
  contractText.value = sampleContract;
  compareText.value = revisedSampleContract;
  contractType.value = "nda";
  jurisdiction.value = "New York";
}

function setMode(mode) {
  appState.mode = mode;
  const isCompare = mode === "compare";
  modeAnalyze.classList.toggle("active", !isCompare);
  modeCompare.classList.toggle("active", isCompare);
  compareInputs.hidden = !isCompare;
  analyzeButton.textContent = isCompare ? "Compare" : "Analyze";
  setStatus(isCompare ? "Compare" : "Ready");
}

function toMarkdown(report) {
  const risks = report.risk_summary?.risks || [];
  const clauses = report.clauses || [];
  return [
    `# Contract Analysis: ${report.metadata?.filename || "contract"}`,
    "",
    report.executive_summary?.one_paragraph || "",
    "",
    "## Risks",
    ...risks.map((risk) => `- **${String(risk.severity || "").toUpperCase()}** (${risk.category}): ${risk.plain_english_explanation}`),
    "",
    "## Clauses",
    ...clauses.map((clause) => `- ${clause.clause_id} **${formatType(clause.clause_type)}** risk ${clause.risk_score}/10`),
  ].join("\n");
}

function toHtml(report) {
  const risks = (report.risk_summary?.risks || []).map((risk) => `<li><strong>${escapeHtml(risk.severity)}</strong>: ${escapeHtml(risk.plain_english_explanation)}</li>`).join("");
  const clauses = (report.clauses || []).map((clause) => `<li>${escapeHtml(clause.clause_id)}: ${escapeHtml(formatType(clause.clause_type))} (${escapeHtml(clause.risk_score)}/10)</li>`).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><title>Contract Analysis</title></head><body><h1>${escapeHtml(report.metadata?.filename || "Contract Analysis")}</h1><p>${escapeHtml(report.executive_summary?.one_paragraph || "")}</p><h2>Risks</h2><ul>${risks}</ul><h2>Clauses</h2><ul>${clauses}</ul></body></html>`;
}

function downloadReport(format) {
  if (!appState.report) {
    setStatus("No report");
    return;
  }
  const data = {
    json: JSON.stringify(appState.report, null, 2),
    markdown: toMarkdown(appState.report),
    html: toHtml(appState.report),
  }[format];
  const type = {
    json: "application/json",
    markdown: "text/markdown",
    html: "text/html",
  }[format];
  const extension = { json: "json", markdown: "md", html: "html" }[format];
  const url = URL.createObjectURL(new Blob([data], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `contract-analysis.${extension}`;
  link.click();
  URL.revokeObjectURL(url);
}

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "Primary contract";
});
compareFileInput.addEventListener("change", () => {
  compareFileName.textContent = compareFileInput.files[0]?.name || "Revised contract";
});
sampleButton.addEventListener("click", loadSample);
analyzeButton.addEventListener("click", () => {
  if (appState.mode === "compare") {
    compareContracts();
  } else {
    analyzeContract();
  }
});
modeAnalyze.addEventListener("click", () => setMode("analyze"));
modeCompare.addEventListener("click", () => setMode("compare"));
clauseSearch.addEventListener("input", renderClauseList);
riskFilter.addEventListener("change", renderClauseList);
exportJson.addEventListener("click", () => downloadReport("json"));
exportMarkdown.addEventListener("click", () => downloadReport("markdown"));
exportHtml.addEventListener("click", () => downloadReport("html"));

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
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(clauseMeshes)[0];
  if (hit) selectClause(hit.object.userData.clause.clause_id);
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
setMode("analyze");
populateScene([
  { clause_id: "C001", clause_type: "confidentiality", risk_score: 2.0, plain_english: "Mutual confidentiality obligations." },
  { clause_id: "C002", clause_type: "termination", risk_score: 2.0, plain_english: "Thirty day termination notice." },
  { clause_id: "C003", clause_type: "liability", risk_score: 6.5, plain_english: "Uncapped liability exposure." },
  { clause_id: "C004", clause_type: "auto_renewal", risk_score: 4.5, plain_english: "Automatic renewal with short notice." },
]);
animate();
