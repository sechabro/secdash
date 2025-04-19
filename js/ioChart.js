import Chart from 'chart.js/auto'

const ctx = document.getElementById('ioChart').getContext('2d');

const ioChart = new Chart(ctx, {
    type: 'bar',
    data: {},
    options: {}
});