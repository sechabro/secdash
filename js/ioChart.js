import Chart from 'chart.js/auto';

document.addEventListener("DOMContentLoaded", () => {
    const ioCtx = document.getElementById('ioChart')?.getContext('2d');
    const cpuCtx = document.getElementById('cpuChart')?.getContext('2d');
    const diskOpsCtx = document.getElementById('diskOpsChart')?.getContext('2d');
    const loadCtx = document.getElementById('loadChart')?.getContext('2d');

    if (!ioCtx || !cpuCtx || !diskOpsCtx || !loadCtx) {
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
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 16 / 9,
            interaction: {
                mode: 'nearest',
                intersect: false,
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time' }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
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
                    fill: false
                },
                {
                    label: 'CPU User (%)',
                    data: [],
                    borderColor: '#ef4444',
                    fill: false
                },
                {
                    label: 'CPU System (%)',
                    data: [],
                    borderColor: '#f59e0b',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 16 / 9,
            interaction: {
                mode: 'nearest',
                intersect: false,
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time' }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    window.diskOpsChart = new Chart(diskOpsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Kilobytes per Transfer (KB/t) - Left',
                    data: [],
                    borderColor: '#10b981',
                    fill: false,
                    yAxisID: 'y'
                },
                {
                    label: 'Transactions per Second (TPS) - Right',
                    data: [],
                    borderColor: '#ef4444',
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 16 / 9,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            stacked: false,
            scales: {
                x: {
                    title: { display: true, text: 'Time' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });

    window.loadChart = new Chart(loadCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '1 Min Load Avg.',
                    data: [],
                    borderColor: '#f59e0b',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 16 / 9,
            interaction: {
                mode: 'nearest',
                intersect: false,
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time' }

                },
                y: {
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
});