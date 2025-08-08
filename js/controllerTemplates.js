export async function asyncGet(endpoint) {
    const connRes = await fetch(endpoint);
    const connData = await connRes.json();
    return connData;
}

export function startStream(streamEndpoint, callback) {
    const eSource = new EventSource(streamEndpoint);
    eSource.onmessage = function (event) {
        if (event.data === "keepalive") return;
        const eventData = JSON.parse(event.data);
        callback(eventData);
    }
}

export async function postWithObj(endpoint, objArgs) {
    try {
        const req = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(objArgs)
        });
        const resp = await req.json();
        return resp;
    } catch (err) {
        console.error("Ipset Call Failed:", err);
        alert("Failed to complete IP status update. See console.")
    }
};