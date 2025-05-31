import { renderWorldMap } from './mapEChart.js';

export let allIpData = [];

export function startIPDataStream() {
    const ipEventSource = new EventSource("/ip-stream");

    ipEventSource.onmessage = function (event) {
        console.log("📡 Received IP data");
        const { ips, country_counts } = JSON.parse(event.data);
        allIpData = ips;
        renderWorldMap(country_counts);
    };

    ipEventSource.onerror = function (err) {
        console.error(`IP Stream Error:`, err)
        ipEventSource.close()
    };
}

//export function waitForNextIPStreamUpdate(callback) {
//    const tempEventSource = new EventSource("/ip-stream");
//
//    tempEventSource.onmessage = function (event) {
//        const { ips } = JSON.parse(event.data);
//        allIpData.splice(0, allIpData.length, ...ips);  // update in-place
//        tempEventSource.close(); // only once
//        callback();
//    };

//    tempEventSource.onerror = function () {
//        console.error("Temporary stream listener failed.");
//        tempEventSource.close();
//    };
//}