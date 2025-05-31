import { MapChart } from 'echarts/charts';
import {
    TitleComponent,
    TooltipComponent,
    VisualMapComponent
} from 'echarts/components';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { countryMap } from './countryMapping.js';
import { allIpData } from './fetchIPS.js';
import { showCountryModal } from './mapModal.js';
import world from './world.json';

echarts.use([
    MapChart,
    TooltipComponent,
    VisualMapComponent,
    TitleComponent,
    CanvasRenderer
]);

echarts.registerMap('world', world);

export const nameToCode = Object.fromEntries(
    Object.entries(countryMap).map(([code, name]) => [name, code])
);

export let mapChart = null;

export function renderWorldMap(country_counts) {
    const mapContainer = document.getElementById('ip-map');
    if (!mapContainer) {
        console.error(`🤢 map container not found: #ip-map`);
        return;
    }

    if (!mapChart) {
        mapChart = echarts.init(mapContainer);
    }

    const allCountryCodes = Object.keys(countryMap);
    const mapData = allCountryCodes.map(code => ({
        name: countryMap[code] || code,
        value: isNaN(country_counts[code]) ? 0 : country_counts[code]
    }));

    const option = {
        title: {
            text: 'Malicious IP Addresses by Country',
            left: 'left',
            top: 20,
            textStyle: {
                fontSize: 22,
                fontWeight: 'bold',
                color: '#1f2937'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} IPs'
        },
        visualMap: {
            min: 0,
            max: Math.max(...mapData.map(d => d.value)) || 1,
            left: 'left',
            top: 'bottom',
            text: ['Max', 'None'],
            itemHeight: 270,
            itemWidth: 25,
            textStyle: {
                fontSize: 14,
                color: '#1f2937'
            },
            calculable: true,
            inRange: {
                color: ['#f8fdff', '#eab308', '#f97316', '#dc2626']
            }
        },
        series: [{
            name: 'Malicious IPs',
            type: 'map',
            map: 'world',
            roam: true,
            data: mapData
        }]
    };

    mapChart.setOption(option);

    mapChart.on('click', function (params) {
        const countryName = params.name;
        const countryCode = nameToCode[countryName];

        if (!countryCode) {
            console.warn(`No country code found for ${countryName}`);
            return;
        }

        const normalizedCodes = {
            "CN": ["CN", "HK", "TW"]
        };
        const targetCodes = normalizedCodes[countryCode] || [countryCode];
        const filtered = allIpData.filter(entry => targetCodes.includes(entry.country));
        showCountryModal(countryName, filtered);
    });
}