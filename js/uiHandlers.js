import { getMapChart } from './mapEChart.js';

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
            if (chart) {
                chart.resize();
            } else {
                console.warn("⚠️ mapChart not initialized yet — resize skipped.");
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
    window.runWhenReady(() => window.startIostatStream());
    window.runWhenReady(() => window.startProcessStream());
    ///window.runWhenReady(() => window.startVisitorStream());
    window.runWhenReady(() => window.startIPDataStream())
    // show visitors tab by default:
    showTab('ip-panel-section');
}

//export async function casesViewSwitch() {
//    document.getElementById("nav-cases").addEventListener("click", async (e) => {
//        e.preventDefault();
//
//        document.getElementById("main-content").classList.add("hidden");
//        document.getElementById("cases-view").classList.remove("hidden");
//
//        await fetchCaseLoad(); //<-- this is async btw.
//    });
//}

//export function liveDashboardSwitch() {
//    document.getElementById("live-dashboard").addEventListener("click", (e) => {
//        e.preventDefault();
//
//        document.getElementById("cases-view").classList.add("hidden");
//        document.getElementById("main-content").classList.remove("hidden");
//    });
//}