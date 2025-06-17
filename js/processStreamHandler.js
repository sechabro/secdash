export function startProcessStream() {
    const evtSource = new EventSource("/process-stream");

    evtSource.onmessage = function (event) {
        const data = JSON.parse(event.data);
        window.renderGroupedProcesses(data);
    };

    return evtSource;
}