import { fetchAndRenderAlertDetail, renderAllAlerts } from "./renderAllAlerts.js";
let toastCount = 0;

export function showToast(alert) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "alert-toast";
    toast.innerText = `${alert.timestamp}: ${alert.msg}`;
    toast.style.animationDelay = `${toastCount * 0.066}s`; // stagger by ~4 frames
    toast.style.pointerEvents = "auto";

    toast.addEventListener("click", async () => {
        // Switch to message center
        document.getElementById("main-content").classList.add("hidden");
        document.getElementById("message-center").classList.remove("hidden");

        // First render the container DOM structure
        await renderAllAlerts();

        // Then inject the specific alert detail
        fetchAndRenderAlertDetail(alert.alert_id);
    });

    container.appendChild(toast);
    toastCount++;

    const totalDuration = 6000 + toastCount * 66;
    setTimeout(() => {
        toast.remove();
    }, totalDuration);

    // Reset counter if container empties
    setTimeout(() => {
        if (container.children.length === 0) toastCount = 0;
    }, totalDuration + 1000);
}