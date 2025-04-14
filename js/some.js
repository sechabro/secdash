async function fetchHostStatus() {
    const hostStatus = await fetch('/host');
    const hostData = await hostStatus.json();
    let hostContent = "<ul>";

    for (const key in hostData) {
        if (typeof hostData[key] === "object" && hostData[key] !== null) {
            hostContent += `<li><strong>${key}:</strong><pre>${JSON.stringify(hostData[key], null, 2)}</pre></li>`;
        } else {
            hostContent += `<li><strong>${key}:</strong> ${hostData[key]}</li>`;
        }
    }

    hostContent += "</ul>";
    document.getElementById('host-status').innerHTML = hostContent;
}
async function fetchData() {
    const visitorRes = await fetch('/visitor');
    const visitorData = await visitorRes.json();
    const { ipdb: { data: ipDetails }, ...rest } = visitorData;
    let visitorContent = "<ul>";

    for (const key in rest) {
        if (typeof rest[key] === "object" && rest[key] !== null) {
            visitorContent += `<li><strong>${key}:</strong><pre>${JSON.stringify(rest[key], null, 2)}</pre></li>`;
        } else {
            visitorContent += `<li><strong>${key}:</strong> ${rest[key]}</li>`;
        }
    }

    visitorContent += "</ul>";

    let abuseIpdb = "<ul>";

    for (const key in ipDetails) {
        if (typeof ipDetails[key] === "object" && ipDetails[key] !== null) {
            abuseIpdb += `<li><strong>${key}:</strong><pre>${JSON.stringify(ipDetails[key], null, 2)}</pre></li>`;
        } else {
            abuseIpdb += `<li><strong>${key}:</strong> ${ipDetails[key]}</li>`;
        }
    }

    abuseIpdb += "</ul>"


    const connRes = await fetch('/connections');
    const connData = await connRes.json();
    const tableBody = document.querySelector('#connections-table tbody');
    connData.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(val => {
            const td = document.createElement('td');
            td.textContent = val;
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });
    document.getElementById('visitor-data').innerHTML = visitorContent;
    document.getElementById('ipdb-data').innerHTML = abuseIpdb;
}

function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tab[onclick*="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'host') {
        fetchHostStatus();  // refresh this tab's content
    }
}

const eventSource = new EventSource("/iostat-stream");

eventSource.onmessage = function (event) {
    const readings = JSON.parse(event.data);  // This is now an array
    //console.log("Raw event data:", event.data);
    const display = readings.map(data =>
        `Date: ${data.date}, Time: ${data.time}, KB/t: ${data.kbt}, TPS: ${data.tps}, MBS: ${data.mbs}, ID No: ${data.idno}`
    ).join('\n');

    document.getElementById("iostat-data").innerText = display;
};

document.querySelector('.collapsible').addEventListener('click', () => {
    const content = document.querySelector('.collapsible-content');
    content.style.display = content.style.display === 'block' ? 'none' : 'block';
});

fetchData();