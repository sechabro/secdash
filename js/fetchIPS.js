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

    return ipEventSource;
}