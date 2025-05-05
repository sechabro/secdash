import Chart from 'chart.js/auto';
import './ioChart.js';
import { fetchHostStatus } from "./fetchHostStatus.js";
import { fetchConnectionsData } from "./fetchConnectionsData.js";
import { renderGroupedProcesses } from './renderGroupedProcesses.js';
import { startIostatStream } from "./iostatStreamHandler.js";
import { startProcessStream } from "./processStreamHandler.js";
import { runWhenReady } from "./runWhenReady.js";
import { initializeUIHandlers } from "./uiHandlers.js";
import { startVisitorStream, connectVisitorStream } from './visitorStreamHandler.js';
import { renderVisitors } from './renderVisitors.js';
import { initVisitorPagination } from './visitorPagination.js';
export {
    fetchHostStatus,
    fetchConnectionsData,
    renderGroupedProcesses,
    startIostatStream,
    startProcessStream,
    startVisitorStream,
    connectVisitorStream,
    runWhenReady,
    initializeUIHandlers,
    renderVisitors,
    initVisitorPagination
};

window.fetchHostStatus = fetchHostStatus;
window.fetchConnectionsData = fetchConnectionsData;
window.renderGroupedProcesses = renderGroupedProcesses;
window.renderVisitors = renderVisitors;
window.startIostatStream = startIostatStream;
window.startProcessStream = startProcessStream;
window.startVisitorStream = startVisitorStream;
window.connectVisitorStream = connectVisitorStream;
window.runWhenReady = runWhenReady;

// ✅ Autostart the dashboard UI
initializeUIHandlers();
initVisitorPagination();