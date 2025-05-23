import { showCaseDetails } from "./caseModal";

export async function fetchCaseLoad() {
    const connRes = await fetch('/flagged-visitors');
    const connData = await connRes.json();

    const caseTable = document.querySelector('.case-listout');
    caseTable.innerHTML = "";  // Clear entire table (thead + tbody)

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    ["Case ID No.", "Visitor ID No.", "Risk Assessment", "Case Creation Date"]
        .forEach(label => {
            const th = document.createElement('th');
            th.textContent = label;
            headerRow.appendChild(th);
        });

    thead.appendChild(headerRow);
    caseTable.appendChild(thead);

    const tbody = document.createElement('tbody');

    connData.forEach(row => {
        const tr = document.createElement('tr');

        const caseIDData = document.createElement('td');
        const visitorIDData = document.createElement('td');
        const riskData = document.createElement('td');
        const createDateData = document.createElement('td');

        caseIDData.innerHTML = `<span class="case-link" data-case-id="${row.id}">${row.id}</span>`;
        caseIDData.querySelector(".case-link").addEventListener("click", () => {
            showCaseDetails(row.id);
        });
        visitorIDData.textContent = row.visitor_id;
        riskData.textContent = row.risk_level;
        createDateData.textContent = row.created_at;

        [caseIDData, visitorIDData, riskData, createDateData].forEach(td => tr.appendChild(td));
        tbody.appendChild(tr);
    });

    caseTable.appendChild(tbody);
}