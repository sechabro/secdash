import { showVisitorAnalysis } from './visitorAnalysisModal.js';

export function renderVisitors(data) {
    const container = document.getElementById("visitor-container");

    container.innerHTML = "";

    data.forEach(visitor => {
        const card = document.createElement("div");
        card.classList.add("user-card");

        const header = document.createElement("div");
        header.classList.add("user-header");
        header.innerHTML = `
            <h3>${visitor.username}</h3>
            <p>${visitor.is_active ? "🟢 Active" : "🟡 Logged out"}</p>
        `;
        card.appendChild(header);

        const tableContainer = document.createElement("div");
        tableContainer.classList.add("table-container");

        const table = document.createElement("table");
        table.innerHTML = `
            <tbody>
                <tr><td>Account Created:</td><td>${visitor.acct_created}</td></tr>
                <tr><td>Last Active:</td><td>${visitor.last_active}</td></tr>
                <tr><td>IP:</td><td>${visitor.ip}</td></tr>
                <tr><td>Geo:</td><td>${visitor.geo_info}</td></tr>
                <tr><td>Device:</td><td>${visitor.device_info}</td></tr>
                <tr><td>Browser:</td><td>${visitor.browser_info}</td></tr>
                <tr><td>Bot:</td><td>${visitor.is_bot}</td></tr>
                <tr><td>Tor:</td><td>${visitor.ipdb}</td></tr>
                <tr><td>Idle (s):</td><td>${visitor.time_idle}</td></tr>
            </tbody>
        `;

        const analyzeButton = document.createElement("button");
        analyzeButton.classList.add("analyze-btn");
        analyzeButton.textContent = "Analyze";

        analyzeButton.addEventListener("click", async () => {
            showVisitorAnalysis(visitor);
        });

        tableContainer.appendChild(table);
        tableContainer.appendChild(analyzeButton);
        card.appendChild(tableContainer);
        container.appendChild(card);
    });
}