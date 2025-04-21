import Chart from 'chart.js/auto';

document.addEventListener("DOMContentLoaded", () => {
    const ioCtx = document.getElementById('ioChart')?.getContext('2d');
    const cpuCtx = document.getElementById('cpuChart')?.getContext('2d');

    if (!ioCtx || !cpuCtx) {
        console.warn("Canvas elements not found");
        return;
    }

    window.ioChart = new Chart(ioCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Throughput (MB/s)',
                    data: [],
                    borderColor: '#00adee',
                    fill: false,
                }
            ]
        },
        options: { responsive: true, animation: false }
    });

    window.cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU Idle (%)',
                    data: [],
                    borderColor: '#10b981',
                    fill: false,
                },
                {
                    label: 'CPU User (%)',
                    data: [],
                    borderColor: '#ef4444',
                    fill: false,
                },
                {
                    label: 'CPU System (%)',
                    data: [],
                    borderColor: '#f59e0b',
                    fill: false,
                }
            ]
        },
        options: { responsive: true, animation: false }
    });
});