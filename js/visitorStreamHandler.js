let evtSource;

export function startVisitorStream() {

    // Initial stream connection
    connectVisitorStream();
    // Event listeners for dropdowns
    const filterFieldSelect = document.getElementById("filter-field");
    const filterParamSelect = document.getElementById("filter-param");

    filterFieldSelect.addEventListener("change", () => {
        document.dispatchEvent(new CustomEvent("visitor-query-changed", {
            detail: {
                filterField: filterFieldSelect.value,
                filterParam: filterParamSelect.value
            }
        }));
    });

    filterParamSelect.addEventListener("change", () => {
        document.dispatchEvent(new CustomEvent("visitor-query-changed", {
            detail: {
                filterField: filterFieldSelect.value,
                filterParam: filterParamSelect.value
            }
        }));
    });
}

export function connectVisitorStream(
    filterField = "is_active",
    filterParam = "true",
    page = 1,
    limit = 9
) {
    if (evtSource) {
        evtSource.close();
    }


    const url = `/visitors?filter_field=${filterField}&filter_param=${filterParam}&page=${page}&limit=${limit}`;
    evtSource = new EventSource(url);

    evtSource.addEventListener("meta", (event) => {
        const meta = JSON.parse(event.data);
        const totalItems = meta.total_items;

        // Dispatch a custom event for pagination module to pick up
        document.dispatchEvent(
            new CustomEvent("visitor-meta-update", {
                detail: { totalItems },
            })
        );
    });

    evtSource.onmessage = function (event) {
        const data = JSON.parse(event.data);
        window.renderVisitors(data);
    };
}