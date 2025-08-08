import { createIPActionButton } from "./ipActionButtons.js";
import { showToast } from './toastManager.js';

export function ioStatRender(ioStatStreamData) {
    if (!window.cpuChart) return;
    cpuChart.data.labels = [];
    cpuChart.data.datasets.forEach(ds => ds.data = []);
    ioStatStreamData.forEach(data => {
        cpuChart.data.labels.push(data.time);
        cpuChart.data.datasets[0].data.push(parseFloat(data.user));
        cpuChart.data.datasets[1].data.push(parseFloat(data.nice));
        cpuChart.data.datasets[2].data.push(parseFloat(data.system));
        cpuChart.data.datasets[3].data.push(parseFloat(data.iowait));
        cpuChart.data.datasets[4].data.push(parseFloat(data.steal));
        cpuChart.data.datasets[5].data.push(parseFloat(data.idle));
    });

    cpuChart.update();
    return;
}

export function renderGroupedProcesses(processStreamData) {
    const container = document.getElementById("process-container");
    const openDropdowns = new Set(
        Array.from(container.querySelectorAll("details[open]"))
            .map(details => details.getAttribute("data-ppidkey"))
    );
    container.innerHTML = "";

    processStreamData.forEach(userGroup => {
        const user = Object.keys(userGroup)[0];
        const ppidData = userGroup[user];
        const card = document.createElement("div");
        card.classList.add("user-card");

        const header = document.createElement("div");
        header.classList.add("user-header");
        header.innerHTML = `<h3>User: ${user}</h3><p>PPIDs: ${Object.keys(ppidData).length}</p>`;
        card.appendChild(header);

        for (const ppid in ppidData) {
            const ppidKey = `${user}-${ppid}`;
            const toggle = document.createElement("details");
            toggle.classList.add("ppid-dropdown");
            toggle.setAttribute("data-ppidkey", ppidKey);

            if (openDropdowns.has(ppidKey)) {
                toggle.setAttribute("open", "");
            }

            const summary = document.createElement("summary");
            summary.textContent = `PPID: ${ppid} (${ppidData[ppid].length} child processes)`;
            toggle.appendChild(summary);

            const tableContainer = document.createElement("div");
            tableContainer.classList.add("table-container");

            const table = document.createElement("table");
            table.innerHTML = `
                <thead>
                    <tr><th>PID</th><th>STAT</th><th>CMD</th></tr>
                </thead>
                <tbody></tbody>
            `;

            const tbody = table.querySelector("tbody");

            ppidData[ppid].forEach(proc => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${proc.pid}</td>
                    <td>${proc.stat}</td>
                    <td>${proc.command}</td>
                `;
                tbody.appendChild(row);
            });

            tableContainer.appendChild(table);
            toggle.appendChild(tableContainer);
            card.appendChild(toggle);
        }

        container.appendChild(card);
    });
}

export function alertStreamRender(alertStreamData) {
    try {
        //const alerts = Array.isArray(alertStreamData) ? alertStreamData : [alertStreamData]; // ensure array

        console.log("📡 Received alert(s):", alertStreamData);
        alertStreamData.forEach(alert => {
            showToast(alert);
        });
    } catch (err) {
        console.error("❌ Failed to parse alert stream message", err);
    }
}


export async function renderAllAlerts() {
    const container = document.getElementById("message-center");
    if (!container) {
        console.warn("❗️Message center container not found.");
        return;
    }

    // Clear previous contents
    container.innerHTML = `
        <h2>📬 Message Center</h2>
        <table class="alert-table">
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Time</th>
                    <th>Type</th>
                    <th>IP</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody id="alert-inbox-body"></tbody>
        </table>
        
    `;

    try {
        const res = await fetch("/all-alerts");
        const alerts = await res.json();

        const tbody = document.getElementById("alert-inbox-body");

        for (const alert of alerts) {
            const row = document.createElement("tr");
            row.classList.add("alert-row");
            row.dataset.alertId = alert.alert_id;
            if (alert.status === "unread") {
                row.classList.add("unread");
            }

            row.innerHTML = `
                <td>${alert.status || "unread"}</td>
                <td>${new Date(alert.timestamp).toLocaleString()}</td>
                <td>${alert.alert_type}</td>
                <td>${alert.ip}</td>
                <td>${alert.msg}</td>
            `;

            row.addEventListener("click", () => fetchAndRenderAlertDetail(alert.alert_id));
            tbody.appendChild(row);
        }
    } catch (err) {
        console.error("🚨 Failed to fetch alerts:", err);
    }
}

export async function fetchAndRenderAlertDetail(alertId) {
    try {
        const res = await fetch(`/alerts/${alertId}`);
        const alert = await res.json();

        // Find the alert row
        const allRows = document.querySelectorAll(".alert-row");
        let parentRow = null;
        for (const row of allRows) {
            if (row.dataset.alertId == alertId) {
                parentRow = row;
                break;
            }
        }

        if (!parentRow) {
            console.warn(`No row found for alert ID ${alertId}`);
            return;
        }

        const existing = document.querySelector(".alert-dropdown");

        // If the existing dropdown belongs to this row, toggle it closed
        if (existing && existing.previousSibling === parentRow) {
            // Animate out before removing
            existing.classList.remove("show");
            setTimeout(() => existing.remove(), 300); // Match transition duration
            return;
        }

        // Otherwise, close any open dropdown
        if (existing) existing.remove();

        // Insert dropdown row below this one
        const detailRow = document.createElement("tr");

        detailRow.classList.add("alert-dropdown");

        detailRow.innerHTML = `
            <td colspan="5">
                <div class="alert-detail-box">
                    <strong>Type:</strong> ${alert.alert_type}<br>
                    <strong>Message:</strong> ${alert.msg}<br>
                    <strong>Status:</strong> ${alert.intel.status}<br>
                    <strong>Risk:</strong> ${alert.intel.risk_level}<br>
                    <strong>Abuse IPDB Score:</strong> ${alert.intel.score}<br>
                    <strong>AI Analysis:</strong> ${alert.intel.analysis}<br>
                    <strong>Action:</strong> ${alert.intel.recommended_action}<br>
                    <strong>Country:</strong> ${alert.intel.country}<br>
                    <strong>Reports:</strong> ${alert.intel.total_reports}<br>
                    <strong>Server Attempts:</strong> ${alert.intel.attempt_count}<br>
                    <strong>First Seen:</strong> ${new Date(alert.intel.first_seen).toLocaleString()}<br>
                    <strong>Last Seen:</strong> ${new Date(alert.intel.last_seen).toLocaleString()}<br><br>
                </div>
            </td>
        `;


        parentRow.insertAdjacentElement("afterend", detailRow);
        const box = detailRow.querySelector(".alert-detail-box");
        const dataForActionBtn = {
            ip: alert.ip,
            country: alert.intel.country,
            status: alert.intel.status
        };
        const actionBtn = await createIPActionButton(dataForActionBtn, alertId);
        box.appendChild(actionBtn);
        // Force reflow to enable animation
        requestAnimationFrame(() => {
            detailRow.classList.add("show");
        });
        // Mark as read
        if (parentRow.classList.contains("unread")) {
            await fetch(`/alerts/${alertId}/mark-read`, { method: "POST" });
            parentRow.classList.remove("unread");
            parentRow.querySelector("td").innerText = "read";
        }

    } catch (err) {
        console.error("❌ Failed to fetch alert details:", err);
    }
}