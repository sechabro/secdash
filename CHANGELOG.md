# Changelog Begins

## [Unreleased] - 2025-05-03

### Added:
- Visitor.ipdb was a major memory hog. Created a `@dataclass(slots=True)` version called VisitorInMem. Reduced memory usage from 2.65mb to 0.67mb
- Implemented `get_field_value()` and `serialize()` helper functions for the universal `stream_delivery()` function, now that we are streaming both dict-based data, and dataclass formats. This required a small change to `stream_delivery()` as well.
- Integrated memory reporting log into `visitor_activity_gen()` to measure and report total usage in MB and by field. Currently commented out.


## [Unreleased] - 2025.05.05
### Added:
- Pagination controls to the visitor dashboard UI (Previous / Next buttons).
- Streamed metadata (`meta` SSE event) from backend to support total item count. `stream_delivery()` now also yields `total_items` in a dedicated `meta` SSE event to aid frontend in determining total page limit per streamed event.
- Automatic disabling of "Next" button when last page is reached.
- `visitorPagination.js` module to manage pagination state and UI sync.

### Changed:
- `visitor-query` bar now styled sticky.

### Fixed
- Pagination state resets to 1 when query parameters (filters) are changed on the visitor dashboard.