const API_BASE = "http://127.0.0.1:8787/api";
let activeScanId = null;
let pollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
    loadToolsStatus();
    loadHistory();

    document.getElementById("targetType").addEventListener("change", (e) => {
        const countryGroup = document.getElementById("countrySelectorGroup");
        const targetInput = document.getElementById("targetInput");
        
        if (e.target.value === "phone") {
            countryGroup.classList.remove("hidden");
            targetInput.placeholder = "7801234567";
        } else {
            countryGroup.classList.add("hidden");
            if (e.target.value === "username") targetInput.placeholder = "username";
            if (e.target.value === "domain") targetInput.placeholder = "example.com";
            if (e.target.value === "ip") targetInput.placeholder = "8.8.8.8";
            if (e.target.value === "email") targetInput.placeholder = "user@example.com";
        }
    });

    document.getElementById("scanForm").addEventListener("submit", startScan);
    document.getElementById("cancelBtn").addEventListener("click", cancelScan);
});

async function loadToolsStatus() {
    try {
        const res = await fetch(`${API_BASE}/tools`);
        const data = await res.json();
        const container = document.getElementById("toolsGrid");
        container.innerHTML = "";

        data.tools.forEach(tool => {
            const item = document.createElement("div");
            item.className = "tool-status-item";
            item.innerHTML = `
                <span>${tool.name}</span>
                <span class="badge ${tool.installed ? 'badge-success' : 'badge-danger'}">
                    ${tool.installed ? 'مثبتة' : 'غير مثبتة'}
                </span>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error(err);
    }
}

async function startScan(e) {
    e.preventDefault();
    const type = document.getElementById("targetType").value;
    let target = document.getElementById("targetInput").value.trim();
    const errorDiv = document.getElementById("errorMessage");

    errorDiv.classList.add("hidden");
    if (type === "phone") {
        target = document.getElementById("countryCode").value + target;
    }

    try {
        const res = await fetch(`${API_BASE}/scan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type, target })
        });
        const data = await res.json();

        if (!res.ok) {
            errorDiv.textContent = data.error;
            errorDiv.classList.remove("hidden");
            return;
        }

        activeScanId = data.scan_id;
        showProgressUI();
        pollInterval = setInterval(checkScanStatus, 2000);
    } catch (err) {
        errorDiv.textContent = "تعذر الاتصال بالمحرك الخلفي";
        errorDiv.classList.remove("hidden");
    }
}

function showProgressUI() {
    document.getElementById("startBtn").disabled = true;
    document.getElementById("cancelBtn").classList.remove("hidden");
    document.getElementById("progressSection").classList.remove("hidden");
    document.getElementById("resultsSection").classList.add("hidden");
    document.getElementById("progressBar").style.width = "20%";
}

async function cancelScan() {
    if (!activeScanId) return;
    await fetch(`${API_BASE}/scan/${activeScanId}/cancel`, { method: "POST" });
    stopProgressUI();
    loadHistory();
}

function stopProgressUI() {
    clearInterval(pollInterval);
    document.getElementById("startBtn").disabled = false;
    document.getElementById("cancelBtn").classList.add("hidden");
    document.getElementById("progressSection").classList.add("hidden");
}

async function checkScanStatus() {
    if (!activeScanId) return;
    try {
        const res = await fetch(`${API_BASE}/scan/${activeScanId}`);
        const scan = await res.json();

        if (scan.status === "completed" || scan.status === "cancelled") {
            stopProgressUI();
            renderResults(scan);
            loadHistory();
        } else {
            document.getElementById("progressBar").style.width = "60%";
        }
    } catch (err) {
        console.error(err);
    }
}

function renderResults(scan) {
    document.getElementById("resultsSection").classList.remove("hidden");
    let totalFindings = 0, successfulTools = 0, totalTime = 0;

    const cardsGrid = document.getElementById("toolCardsGrid");
    const tableBody = document.getElementById("findingsTableBody");
    cardsGrid.innerHTML = "";
    tableBody.innerHTML = "";

    scan.results.forEach(res => {
        totalFindings += res.findings_count;
        if (res.status === "Completed") successfulTools++;
        totalTime += res.execution_time;

        const card = document.createElement("div");
        card.className = "tool-res-card";
        card.innerHTML = `
            <h4>${res.tool_name}</h4>
            <p>الحالة: <span class="badge ${res.status === 'Completed' ? 'badge-success' : 'badge-danger'}">${res.status}</span></p>
            <p>النتائج: ${res.findings_count}</p>
            <p>الوقت: ${res.execution_time}s</p>
            <button onclick="viewRaw('${res.tool_name}', \`${escapeQuotes(res.raw_output)}\`)" class="btn btn-secondary" style="margin-top:10px; width:100%;">عرض Raw Output</button>
        `;
        cardsGrid.appendChild(card);

        res.parsed_results.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.source || '-'}</td>
                <td>${item.type || '-'}</td>
                <td style="font-family: monospace;">${item.value}</td>
                <td>${res.tool_name}</td>
                <td>${item.confidence || 'Medium'}</td>
            `;
            tableBody.appendChild(row);
        });
    });

    document.getElementById("metricTotal").textContent = totalFindings;
    document.getElementById("metricToolsCount").textContent = successfulTools;
    document.getElementById("metricTime").textContent = `${totalTime.toFixed(1)}s`;
}

function escapeQuotes(str) {
    return (str || '').replace(/`/g, '\\`').replace(/\${/g, '\\${');
}

function viewRaw(toolName, raw) {
    document.getElementById("modalToolTitle").textContent = `Raw Output - ${toolName}`;
    document.getElementById("rawOutputCode").textContent = raw || "لا توجد مخرجات.";
    document.getElementById("rawModal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("rawModal").classList.add("hidden");
}

function copyRawOutput() {
    navigator.clipboard.writeText(document.getElementById("rawOutputCode").textContent);
    alert("تم النسخ بنجاح.");
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/history`);
        const data = await res.json();
        const body = document.getElementById("historyTableBody");
        body.innerHTML = "";

        data.history.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.target_type}</td>
                <td>${item.target}</td>
                <td>${item.created_at}</td>
                <td><span class="badge ${item.status === 'completed' ? 'badge-success' : 'badge-danger'}">${item.status}</span></td>
                <td>
                    <button onclick="loadPreviousScan('${item.id}')" class="btn btn-secondary">عرض</button>
                    <button onclick="deleteScan('${item.id}')" class="btn btn-danger">حذف</button>
                </td>
            `;
            body.appendChild(row);
        });
    } catch (err) {
        console.error(err);
    }
}

async function loadPreviousScan(scanId) {
    const res = await fetch(`${API_BASE}/scan/${scanId}`);
    renderResults(await res.json());
}

async function deleteScan(scanId) {
    if (!confirm("تأكيد الحذف؟")) return;
    await fetch(`${API_BASE}/scan/${scanId}/delete`, { method: "DELETE" });
    loadHistory();
}

function exportResults(fmt) {
    if (!activeScanId) return;
    window.open(`${API_BASE}/scan/${activeScanId}/export?format=${fmt}`, '_blank');
}