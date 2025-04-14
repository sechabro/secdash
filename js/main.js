import { fetchHostStatus } from './host.js';
import { fetchData } from './visitor.js';
import { startIostatStream } from './iostat.js';
import { setupTabs } from './tabs.js';
import { fetchVisitorData } from './visitor.js';
import { fetchConnectionsData } from './connections.js';

document.addEventListener("DOMContentLoaded", () => {
    fetchHostStatus();
    fetchData();
    startIostatStream();
    setupTabs();
    fetchVisitorData();
    fetchConnectionsData();
});