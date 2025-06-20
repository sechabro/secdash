export function startIostatStream() {
    const iostatEventSource = new EventSource("/iostat-stream");

    iostatEventSource.onmessage = function (event) {
        if (event.data === "keepalive") return;

        const readings = JSON.parse(event.data);
        if (!window.cpuChart) return;

        cpuChart.data.labels = [];
        cpuChart.data.datasets.forEach(ds => ds.data = []);

        readings.forEach(data => {
            cpuChart.data.labels.push(data.time);
            cpuChart.data.datasets[0].data.push(parseFloat(data.user));
            cpuChart.data.datasets[1].data.push(parseFloat(data.nice));
            cpuChart.data.datasets[2].data.push(parseFloat(data.system));
            cpuChart.data.datasets[3].data.push(parseFloat(data.iowait));
            cpuChart.data.datasets[4].data.push(parseFloat(data.steal));
            cpuChart.data.datasets[5].data.push(parseFloat(data.idle));

        });

        cpuChart.update();
    };

    return iostatEventSource;
}