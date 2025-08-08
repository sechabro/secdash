import { postWithObj } from "./controllerTemplates.js";
import { allIpData } from "./fetchIPS.js";
import { getMapChart, nameToCode } from "./mapEChart.js";

export function showCountryModal(countryName, ipData) {
    const overlay = document.getElementById("country-modal-overlay");
    const title = document.getElementById("country-modal-title");
    const list = document.getElementById("country-ip-list");
    const closeBtn = document.getElementById("country-modal-close-btn");
    const tableBody = document.querySelector("#country-modal-content .connections-table tbody");

    title.textContent = countryName;
    tableBody.innerHTML = "";

    const skipKeys = new Set(["country", "first_seen", "last_seen", "ip_id"]);
    ipData.forEach(ip => {
        const tr = document.createElement("tr");

        Object.entries(ip).forEach(([key, val]) => {
            if (skipKeys.has(key)) return;
            const td = document.createElement("td");
            td.textContent = val;
            tr.appendChild(td);
        });

        const actionTd = document.createElement("td");
        const btn = document.createElement("button");
        btn.textContent = ip.status === "active" ? "Ban" : "Restore";
        btn.classList.add("ip-action-btn");
        btn.classList.add(ip.status === "active" ? "ban-btn" : "restore-btn");


        btn.onclick = async () => {
            btn.disabled = true;

            const iPObj = {
                ip: ip.ip,
                status: ip.status === "active" ? "banned" : "active"
            };

            const result = await postWithObj("/ipset-calling", iPObj);

            if (result) {
                alert(`${iPObj.ip} has been ${result.status}. DB update: ${result.db_update}`);
            } else {
                alert(`Failed to update status for ${iPObj.ip}`);
            }

            // force a refresh to push out stale data.
            setTimeout(() => {
                console.log("⏱️ Timeout fired — attempting to refresh modal.");

                const countryCode = nameToCode[countryName];

                const normalizedCodes = {
                    "CN": ["CN", "HK", "TW"]
                };
                const targetCodes = normalizedCodes[countryCode] || [countryCode];
                //console.log("🔍 Target country codes:", targetCodes);
                //console.log("📦 Current allIpData snapshot:", allIpData);

                const updatedData = allIpData.filter(entry => targetCodes.includes(entry.country));

                console.log("📊 Filtered updatedData:", updatedData);

                if (updatedData.length === 0) {
                    console.warn("⚠️ No matching IPs found — aborting refresh.");
                    return;
                }

                console.log("✅ Recalling showCountryModal with updatedData");
                showCountryModal(countryName, updatedData);
            }, 500);

            btn.disabled = false;
        };

        actionTd.appendChild(btn);
        tr.appendChild(actionTd);
        tableBody.appendChild(tr);
    });

    overlay.classList.remove("hidden");

    closeBtn.onclick = () => overlay.classList.add("hidden");
    window.onclick = (e) => { if (e.target === overlay) overlay.classList.add("hidden"); };

    setTimeout(() => {
        const mapChart = getMapChart();
        if (mapChart) {
            mapChart.resize();
        } else {
            console.warn("mapChart still not initialized.");
        }
    }, 100);
};