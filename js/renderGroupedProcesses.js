export function renderGroupedProcesses(data) {
    const container = document.getElementById("process-container");
    const openDropdowns = new Set(
        Array.from(container.querySelectorAll("details[open]"))
            .map(details => details.getAttribute("data-ppidkey"))
    );
    container.innerHTML = "";

    data.forEach(userGroup => {
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