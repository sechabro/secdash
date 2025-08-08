//import { startAlertStream } from './alertStreamHandler.js';
import { startStream } from './controllerTemplates.js';
import { fetchConnectionsData } from "./fetchConnectionsData.js";
import { fetchHostStatus } from "./fetchHostStatus.js";
import { startIPDataStream } from "./fetchIPS.js";
import './ioChart.js';
//import { startIostatStream } from "./iostatStreamHandler.js";
//import { startProcessStream } from "./processStreamHandler.js";
//import { renderGroupedProcesses } from './renderGroupedProcesses.js';
import { runWhenReady } from "./runWhenReady.js";
import { initializeUIHandlers } from "./uiHandlers.js";
//import { initVisitorPagination } from './visitorPagination.js';
//import { connectVisitorStream, startVisitorStream } from './visitorStreamHandler.js';

export {
    fetchConnectionsData,
    fetchHostStatus,
    initializeUIHandlers,
    runWhenReady,
    startIPDataStream,
    startStream
};

window.fetchHostStatus = fetchHostStatus;
window.fetchConnectionsData = fetchConnectionsData;
window.startStream = startStream;
window.startIPDataStream = startIPDataStream;
window.runWhenReady = runWhenReady;


window.closeAllStreams = function () {
    if (window.alertStream) window.alertStream.close();
    if (window.iostatStream) window.iostatStream.close();
    if (window.processStream) window.processStream.close();
    if (window.ipStream) window.ipStream.close();
    console.log("Streams closed");
};

// ✅ Autostart the dashboard UI
initializeUIHandlers();