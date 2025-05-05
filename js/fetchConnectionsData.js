export async function fetchConnectionsData() {
    const connRes = await fetch('/connections');
    const connData = await connRes.json();
    const tableBody = document.querySelector('.connections-table tbody');
    tableBody.innerHTML = "";  // Clear existing rows first
    connData.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(val => {
            const td = document.createElement('td');
            td.textContent = val;
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
}