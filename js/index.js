import Chart from 'chart.js/auto';
import './ioChart.js';
import { fetchHostStatus } from "./fetchHostStatus.js";
import { fetchVisitorData } from "./fetchVisitorData.js";
import { fetchConnectionsData } from "./fetchConnectionsData.js";
import { renderGroupedProcesses } from './renderGroupedProcesses.js';
import { startIostatStream } from "./iostatStreamHandler.js";
import { startProcessStream } from "./processStreamHandler.js";
import { runWhenReady } from "./runWhenReady.js";
import { initializeUIHandlers } from "./uiHandlers.js";

export {
    fetchHostStatus,
    fetchVisitorData,
    fetchConnectionsData,
    renderGroupedProcesses,
    startIostatStream,
    startProcessStream,
    runWhenReady,
    initializeUIHandlers
};

window.fetchHostStatus = fetchHostStatus;
window.fetchVisitorData = fetchVisitorData;
window.fetchConnectionsData = fetchConnectionsData;
window.renderGroupedProcesses = renderGroupedProcesses;
window.startIostatStream = startIostatStream;
window.startProcessStream = startProcessStream;
window.runWhenReady = runWhenReady;

// ✅ Autostart the dashboard UI
initializeUIHandlers();