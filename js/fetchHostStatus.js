export async function fetchHostStatus() {
    // Wait until DOM is fully loaded (if not already)
    if (document.readyState === 'loading') {
        await new Promise(resolve =>
            document.addEventListener('DOMContentLoaded', resolve, { once: true })
        );
    }

    const hostStatus = await fetch('/host');
    const data = await hostStatus.json();

    const uptime = data.uptime_seconds;
    const days = Math.floor(uptime / 86400);
    const hours = Math.floor((uptime % 86400) / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);

    const loadAvg = data.load_avg.map(n => n.toFixed(1)).join(" / ");

    const hostPanelHtml = `
        <div class="host-strip">
            <div><strong>CPU:</strong> ${data.cpu_percent}%</div>
            <div><strong>MEM:</strong> ${data.memory_percent}%</div>
            <div><strong>DISK:</strong> ${data.disk_percent}%</div>
            <div><strong>UPTIME:</strong> ${days}d ${hours}h ${minutes}m</div>
            <div><strong>LOAD:</strong> ${loadAvg}</div>
            <div><strong>CORES:</strong> ${data.physical_cores}/${data.logical_cores}</div>
            <div><strong>RAM:</strong> ${data.memory_gb}GB</div>
        </div>
    `;

    const target = document.getElementById('host-status');
    if (target) {
        target.innerHTML = hostPanelHtml;
    } else {
        console.warn("Could not find #host-status to insert host panel HTML.");
    }
}