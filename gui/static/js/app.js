// ── DOM refs ──
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const tokenInput = $("#token-input");
const btnVerify = $("#btn-verify");
const verifyStatus = $("#verify-status");
const stepServers = $("#step-servers");
const sourceSelect = $("#source-server");
const targetSelect = $("#target-server");
const btnClone = $("#btn-clone");
const cloneStatus = $("#clone-status");
const stepProgress = $("#step-progress");
const progressBar = $("#progress-bar");
const progressText = $("#progress-text");
const stepResults = $("#step-results");
const resultSummary = $("#result-summary");
const mappingTable = $("#mapping-table-container");
const toast = $("#toast");

// ── Socket.IO ──
const socket = io();

socket.on("progress", (data) => {
  stepProgress.classList.remove("hidden");
  progressBar.style.width = data.percent + "%";
  progressText.textContent = data.message;
});

socket.on("clone_complete", (data) => {
  showResults(data.mapping);
});

socket.on("clone_error", (data) => {
  toastShow("Clone failed: " + data.error, "error");
  stepProgress.classList.add("hidden");
  btnClone.disabled = false;
});

// ── Verify Token ──
btnVerify.addEventListener("click", async () => {
  const token = tokenInput.value.trim();
  if (!token) {
    verifyStatus.className = "status error";
    verifyStatus.textContent = "Please enter a token.";
    return;
  }
  btnVerify.disabled = true;
  verifyStatus.className = "status info";
  verifyStatus.textContent = "Verifying...";

  try {
    const resp = await fetch("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    const data = await resp.json();
    if (data.ok) {
      verifyStatus.className = "status success";
      verifyStatus.textContent = `Logged in as ${data.user} — found ${data.guilds.length} manageable server(s).`;
      populateGuilds(data.guilds);
      stepServers.classList.remove("hidden");
    } else {
      verifyStatus.className = "status error";
      verifyStatus.textContent = "Error: " + data.error;
    }
  } catch (e) {
    verifyStatus.className = "status error";
    verifyStatus.textContent = "Network error: " + e.message;
  } finally {
    btnVerify.disabled = false;
  }
});

// ── Populate guild dropdowns ──
function populateGuilds(guilds) {
  sourceSelect.innerHTML = '<option value="">-- Select source server --</option>';
  targetSelect.innerHTML = '<option value="">-- Select target server --</option>';
  guilds.forEach((g) => {
    const opt = `<option value="${g.id}">${g.name}</option>`;
    sourceSelect.insertAdjacentHTML("beforeend", opt);
    targetSelect.insertAdjacentHTML("beforeend", opt);
  });
}

// ── Enable clone button when both selected ──
[sourceSelect, targetSelect].forEach((sel) =>
  sel.addEventListener("change", () => {
    btnClone.disabled = !(sourceSelect.value && targetSelect.value);
    cloneStatus.textContent = "";
  })
);

// ── Start Clone ──
btnClone.addEventListener("click", async () => {
  const sourceId = sourceSelect.value;
  const targetId = targetSelect.value;
  if (!sourceId || !targetId) return;
  if (sourceId === targetId) {
    cloneStatus.className = "status error";
    cloneStatus.textContent = "Source and target must be different servers.";
    return;
  }

  btnClone.disabled = true;
  cloneStatus.className = "status info";
  cloneStatus.textContent = "Starting clone...";
  stepResults.classList.add("hidden");
  stepProgress.classList.remove("hidden");
  progressBar.style.width = "0%";
  progressText.textContent = "Connecting...";

  try {
    const resp = await fetch("/api/clone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_id: sourceId,
        target_id: targetId,
      }),
    });
    const data = await resp.json();
    if (!data.ok) {
      toastShow("Error: " + data.error, "error");
      stepProgress.classList.add("hidden");
      btnClone.disabled = false;
    }
  } catch (e) {
    toastShow("Network error: " + e.message, "error");
    stepProgress.classList.add("hidden");
    btnClone.disabled = false;
  }
});

// ── Show Results ──
let lastMapping = null;

function showResults(mapping) {
  lastMapping = mapping;
  stepProgress.classList.add("hidden");
  stepResults.classList.remove("hidden");
  btnClone.disabled = false;
  cloneStatus.className = "status success";
  cloneStatus.textContent = "Clone complete!";

  const entries = Object.values(mapping);
  const ok = entries.filter((e) => !e.error).length;
  const err = entries.filter((e) => e.error).length;
  resultSummary.innerHTML = `
    <div>Total channels cloned: <span class="ok">${entries.length}</span></div>
    <div>Successful: <span class="ok">${ok}</span> &nbsp;|&nbsp;
         Failed: <span class="${err > 0 ? 'err' : ''}">${err}</span></div>
  `;

  buildTable(mapping);
}

function buildTable(mapping) {
  let html = `<table>
    <thead><tr>
      <th>Source Channel</th><th>Source Webhook</th>
      <th>Target Channel</th><th>Target Webhook</th>
      <th>Type</th><th>Status</th>
    </tr></thead><tbody>`;

  for (const [id, info] of Object.entries(mapping)) {
    const status = info.error
      ? `<span style="color:var(--red)">ERROR</span>`
      : `<span style="color:var(--green)">OK</span>`;
    const truncate = (s, n = 50) => (s && s.length > n ? s.slice(0, n) + "…" : s || "—");
    html += `<tr>
      <td title="${info.source_name || ''}">${truncate(info.source_name, 30)}</td>
      <td title="${info.source_webhook_url || ''}">${truncate(info.source_webhook_url)}</td>
      <td title="${info.target_name || ''}">${truncate(info.target_name || 'FAILED', 30)}</td>
      <td title="${info.target_webhook_url || ''}">${truncate(info.target_webhook_url)}</td>
      <td>${info.type || '?'}</td>
      <td>${status}</td>
    </tr>`;
  }
  html += "</tbody></table>";
  mappingTable.innerHTML = html;
}

// ── Export ──
async function exportMapping(format) {
  try {
    const resp = await fetch(`/api/export?format=${format}`);
    const data = await resp.json();
    if (data.ok) {
      await navigator.clipboard.writeText(data.data);
      toastShow(`Copied ${format.toUpperCase()} to clipboard!`, "success");
    }
  } catch (e) {
    toastShow("Export failed: " + e.message, "error");
  }
}

function downloadMapping(format) {
  const ext = format === "markdown" ? "md" : format;
  window.open(`/api/export/download?format=${format}`, "_blank");
}

// ── Toast ──
function toastShow(msg, type) {
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  toast.classList.remove("hidden");
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => toast.classList.add("hidden"), 3000);
}
