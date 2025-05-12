export function startIostatStream() {
    const iostatEventSource = new EventSource("/iostat-stream");

    iostatEventSource.onmessage = function (event) {
        const readings = JSON.parse(event.data);
        if (!window.ioChart || !window.cpuChart || !window.diskOpsChart || !window.loadChart) return;

        ioChart.data.labels = [];
        ioChart.data.datasets[0].data = [];

        cpuChart.data.labels = [];
        cpuChart.data.datasets.forEach(ds => ds.data = []);

        diskOpsChart.data.labels = [];
        diskOpsChart.data.datasets.forEach(ds => ds.data = []);

        loadChart.data.labels = [];
        loadChart.data.datasets[0].data = [];

        readings.forEach(data => {
            ioChart.data.labels.push(data.time);
            cpuChart.data.labels.push(data.time);
            diskOpsChart.data.labels.push(data.time);
            loadChart.data.labels.push(data.time);

            ioChart.data.datasets[0].data.push(parseFloat(data.throughput_mbs));

            cpuChart.data.datasets[0].data.push(parseFloat(data.cpu_idle_pct));
            cpuChart.data.datasets[1].data.push(parseFloat(data.cpu_user_pct));
            cpuChart.data.datasets[2].data.push(parseFloat(data.cpu_system_pct));

            diskOpsChart.data.datasets[0].data.push(parseFloat(data.kbt));
            diskOpsChart.data.datasets[1].data.push(parseInt(data.tps));

            loadChart.data.datasets[0].data.push(parseFloat(data.load_avg_1m));
        });

        ioChart.update();
        cpuChart.update();
        diskOpsChart.update();
        loadChart.update();
    };
}