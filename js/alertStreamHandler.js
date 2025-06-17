import { showToast } from './toastManager.js';

export function startAlertStream() {
    console.log("Alert stream initialized");

    const alertSource = new EventSource('/alert-stream');

    alertSource.onmessage = (event) => {
        if (event.data === "keepalive") {
            // keep the stream connected, but do nothing
            console.log("keepalive notification")
            return;
        }

        try {
            const data = JSON.parse(event.data);
            const alerts = Array.isArray(data) ? data : [data]; // ensure array

            console.log("📡 Received alert(s):", alerts);
            alerts.forEach(alert => {
                showToast(alert);
            });
        } catch (err) {
            console.error("❌ Failed to parse alert stream message", err);
        }
    };

    alertSource.onerror = (err) => {
        console.error("⚠️ Alert stream error:", err);
        alertSource.close(); // Optional: close on error, or attempt reconnect
    };

    return alertSource;
}