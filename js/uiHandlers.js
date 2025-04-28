export function initializeUIHandlers() {
    // COLLAPSIBLE HANDLER
    document.querySelector('.collapsible').addEventListener('click', () => {
        const content = document.querySelector('.collapsible-content');
        content.classList.toggle('visible');
    });

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
    window.runWhenReady(() => window.fetchVisitorData());
}