import { iPSetCall } from "./iPSetCall.js";
import { showCountryModal } from "./mapModal.js";
import { fetchAndRenderAlertDetail } from "./renderAllAlerts.js";

const callbacks = {
    fetchAndRenderAlertDetail,
    showCountryModal
}

export async function createIPActionButton(ip, alertId = null, callback = null) {


    const btn = document.createElement("button");
    btn.textContent = ip.status === "active" ? "Ban" : "Restore";
    btn.classList.add("ip-action-btn");
    btn.classList.add(ip.status === "active" ? "ban-btn" : "restore-btn");

    btn.onclick = async () => {
        btn.disabled = true;

        const iPObj = {
            ip: ip.ip,
            status: ip.status === "active" ? "banned" : "active"
        };
        const result = await iPSetCall(iPObj);

        if (result) {
            if (iPObj.status === "active") {
                alert(`${iPObj.ip} restore result: ${result.status}. DB update: ${result.db_update}`);
            } else {
                alert(`${iPObj.ip} has been ${result.status}. DB update: ${result.db_update}`);
            }

        } else {
            alert(`Failed to update status for ${iPObj.ip}`);
        }

        if (alertId) {
            setTimeout(() => {
                // ⏱️ Auto-refresh this alert row
                fetchAndRenderAlertDetail(alertId);
            }, 500);
        }

        btn.disabled = false;
    };

    return btn;
}