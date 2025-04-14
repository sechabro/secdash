export function startIostatStream() {
    const eventSource = new EventSource("/iostat-stream");

    eventSource.onmessage = function (event) {
        const readings = JSON.parse(event.data);
        const display = readings.map(data =>
            `Date: ${data.date}, Time: ${data.time}, KB/t: ${data.kbt}, TPS: ${data.tps}, MBS: ${data.mbs}, ID No: ${data.idno}`
        ).join('\n');

        document.getElementById("iostat-data").innerText = display;
    };
}