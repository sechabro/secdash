export function startProcessStream() {
    const evtSource = new EventSource("/process-stream");

    evtSource.onmessage = function (event) {
        if (event.data === "keepalive") return;
        const data = JSON.parse(event.data);
        window.renderGroupedProcesses(data);
    };

    return evtSource;
}