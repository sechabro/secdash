export function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');

            // Remove active class from all tabs and content sections
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            // Add active class to the selected tab and content
            tab.classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // Fetch dynamic data for the "host" tab
            if (tabId === 'host') {
                fetchHostStatus();
            }

            if (tabId === 'visitor') {
                fetchVisitorData();
            }

            if (tabId === 'connections') {
                fetchConnectionsData();
            }
        });
    });
}