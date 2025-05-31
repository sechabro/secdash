import Chart from 'chart.js/auto';

document.addEventListener("DOMContentLoaded", () => {
    const cpuCtx = document.getElementById('cpuChart')?.getContext('2d');

    if (!cpuCtx) {
        console.warn("Canvas elements not found");
        return;
    }

    window.cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Idle (%)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    fill: true
                },
                {
                    label: 'User (%)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    fill: true
                },
                {
                    label: 'Nice (%)',
                    data: [],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    fill: true
                },
                {
                    label: 'System (%)',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    fill: true
                },
                {
                    label: 'I/O Wait (%)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    fill: true
                },
                {
                    label: 'Steal (%)',
                    data: [],
                    borderColor: '#ec4899',
                    backgroundColor: 'rgba(236, 72, 153, 0.2)',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2 / 1,
            interaction: {
                mode: 'nearest',
                intersect: false,
            },
            scales: {
                x: {
                    stacked: false,
                    title: { display: true, text: 'Time' }
                },
                y: {
                    stacked: false,
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'CPU %' }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ${context.raw.toFixed(2)}%`;
                        }
                    }
                }
            }
        }
    });
});