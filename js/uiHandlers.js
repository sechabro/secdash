import { getMapChart } from './mapEChart.js';
import { renderAllAlerts } from './renderAllAlerts.js';

export function initializeUIHandlers() {
    // TAB SWITCHING HANDLER
    function showTab(tabId) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
        document.querySelector(`.tab[onclick*="${tabId}"]`).classList.add('active');
        document.getElementById(tabId).classList.add('active');

        if (tabId === 'host') {
            window.fetchHostStatus();
        } else if (tabId === 'connections') {
            window.runWhenReady(() => window.fetchConnectionsData());
        } else if (tabId === 'ip-panel-section') {
            const chart = getMapChart();
            const spinner = document.getElementById("wait-spinner-analysis");
            if (chart) {
                chart.resize();
            } else {
                if (spinner) spinner.classList.remove("hidden");

                // Listen for map to finish loading
                window.addEventListener("map-ready", () => {
                    const mapChart = getMapChart();
                    if (mapChart) {
                        mapChart.resize();
                    }
                    if (spinner) spinner.classList.add("hidden");
                }, { once: true });
            }
        }
    }
    window.showTab = showTab;  // Expose globally for your <div onclick="showTab('...')">

    // SIDEBAR TOGGLE HANDLER
    const toggleBtn = document.getElementById('toggle-btn');
    const sidebar = document.getElementById('sidebar');

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        sidebar.classList.toggle('closed');
    });

    // SSE STREAMS AND START TRIGGERS
    window.runWhenReady(() => { window.alertStream = startAlertStream(); });
    window.runWhenReady(() => { window.iostatStream = startIostatStream(); });
    window.runWhenReady(() => { window.processStream = startProcessStream(); });
    window.runWhenReady(() => { window.ipStream = startIPDataStream(); });

    // show visitors tab by default:
    showTab('ip-panel-section');
    messageCenterSwitch();
    liveDashboardSwitch();
}

export function messageCenterSwitch() {
    document.getElementById("message-center-sidebar").addEventListener("click", (e) => {
        e.preventDefault();

        document.getElementById("main-content").classList.add("hidden");
        document.getElementById("message-center").classList.remove("hidden");
        renderAllAlerts();
    });
}

export function liveDashboardSwitch() {
    document.getElementById("live-dashboard").addEventListener("click", (e) => {
        e.preventDefault();

        document.getElementById("message-center").classList.add("hidden");
        document.getElementById("main-content").classList.remove("hidden");
    });
}