let currentPage = 1;
const limit = 9;
let lastKnownTotalPages = null;

export function initVisitorPagination() {
    const controls = document.getElementById("pagination-controls");
    const pageLabel = document.getElementById("page-number");
    const prevBtn = document.getElementById("prev-page");
    const nextBtn = document.getElementById("next-page");

    function updateStream() {
        const filterField = document.getElementById("filter-field").value;
        const filterParam = document.getElementById("filter-param").value;

        window.connectVisitorStream(filterField, filterParam, currentPage, limit);

        pageLabel.textContent = `Page ${currentPage}`;

        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled =
            lastKnownTotalPages !== null && currentPage >= lastKnownTotalPages;
    }

    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            updateStream();
        }
    });

    nextBtn.addEventListener("click", () => {
        if (
            lastKnownTotalPages !== null &&
            currentPage >= lastKnownTotalPages
        ) {
            return; // Block going past last page
        }

        currentPage++;
        updateStream();
    });

    // Listen to meta updates from the stream to update known total pages
    document.addEventListener("visitor-meta-update", (e) => {
        const totalItems = e.detail.totalItems;
        lastKnownTotalPages = Math.ceil(totalItems / limit);
        // Ensure next button reflects up-to-date info
        nextBtn.disabled = currentPage >= lastKnownTotalPages;
    });

    updateStream(); // kick off the first page
}