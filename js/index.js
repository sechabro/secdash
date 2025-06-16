import { startAlertStream } from './alertStreamHandler.js';
import { fetchConnectionsData } from "./fetchConnectionsData.js";
import { fetchHostStatus } from "./fetchHostStatus.js";
import { startIPDataStream } from "./fetchIPS.js";
import './ioChart.js';
import { startIostatStream } from "./iostatStreamHandler.js";
import { startProcessStream } from "./processStreamHandler.js";
import { renderGroupedProcesses } from './renderGroupedProcesses.js';
import { runWhenReady } from "./runWhenReady.js";
import { initializeUIHandlers } from "./uiHandlers.js";
//import { initVisitorPagination } from './visitorPagination.js';
//import { connectVisitorStream, startVisitorStream } from './visitorStreamHandler.js';

export {
    fetchConnectionsData,
    fetchHostStatus,
    initializeUIHandlers,
    renderGroupedProcesses,
    runWhenReady, startAlertStream, startIostatStream,
    startIPDataStream,
    startProcessStream
};

window.fetchHostStatus = fetchHostStatus;
window.fetchConnectionsData = fetchConnectionsData;
window.renderGroupedProcesses = renderGroupedProcesses;
//window.renderVisitors = renderVisitors;
window.startIostatStream = startIostatStream;
window.startProcessStream = startProcessStream;
//window.startVisitorStream = startVisitorStream;
window.startIPDataStream = startIPDataStream;
//window.connectVisitorStream = connectVisitorStream;
window.runWhenReady = runWhenReady;

// ✅ Autostart the dashboard UI
initializeUIHandlers();
startAlertStream();
//initVisitorPagination();
//casesViewSwitch();
//liveDashboardSwitch();