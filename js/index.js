import { fetchConnectionsData } from "./fetchConnectionsData.js";
import { fetchHostStatus } from "./fetchHostStatus.js";
import './ioChart.js';
import { startIostatStream } from "./iostatStreamHandler.js";
import { startProcessStream } from "./processStreamHandler.js";
import { renderGroupedProcesses } from './renderGroupedProcesses.js';
import { renderVisitors } from './renderVisitors.js';
import { runWhenReady } from "./runWhenReady.js";
import { casesViewSwitch, initializeUIHandlers, liveDashboardSwitch } from "./uiHandlers.js";
import { initVisitorPagination } from './visitorPagination.js';
import { connectVisitorStream, startVisitorStream } from './visitorStreamHandler.js';

export {
    casesViewSwitch,
    connectVisitorStream,
    fetchConnectionsData,
    fetchHostStatus,
    initializeUIHandlers,
    initVisitorPagination,
    liveDashboardSwitch,
    renderGroupedProcesses,
    renderVisitors,
    runWhenReady,
    startIostatStream,
    startProcessStream,
    startVisitorStream
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
casesViewSwitch();
liveDashboardSwitch();