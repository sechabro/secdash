import { createIPActionButton } from "./ipActionButtons.js";

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
