export function startVisitorStream() {
    let evtSource = null;

    function connectStream(filterField = "is_active", filterParam = "true") {
        if (evtSource) {
            evtSource.close();
        }

        const url = `/visitors?filter_field=${filterField}&filter_param=${filterParam}`;
        evtSource = new EventSource(url);

        evtSource.onmessage = function (event) {
            const data = JSON.parse(event.data);
            //console.log("Visitor data received:", data);
            window.renderVisitors(data);
        };
    }

    // Initial stream connection
    connectStream();
    // Event listeners for dropdowns
    const filterFieldSelect = document.getElementById("filter-field");
    const filterParamSelect = document.getElementById("filter-param");

    filterFieldSelect.addEventListener("change", () => {
        connectStream(filterFieldSelect.value, filterParamSelect.value);
    });

    filterParamSelect.addEventListener("change", () => {
        connectStream(filterFieldSelect.value, filterParamSelect.value);
    });
}