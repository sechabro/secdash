async function fetchConnectionsData() {
    try {
        const response = await fetch('/connections');
        const data = await response.json();
        const tableBody = document.querySelector('#connections-table tbody');

        // Clear previous data
        tableBody.innerHTML = "";

        data.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(val => {
                const td = document.createElement('td');
                td.textContent = val;
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching connection data:', error);
    }
}