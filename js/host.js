export async function fetchHostStatus() {
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