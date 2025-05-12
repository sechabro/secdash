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


## [Unreleased] - 2025.05.06
### Changed:
- Optimized the in-memory I/O stats stream by replacing dictionary-based entries with a leaner, slot-based dataclass model.

## [Unreleased] - 2025.05.08
### Added:
- `/visitor-analysis` POST endpoint for GPT-4-driven visitor risk evaluation.
- Manual "Analyze" button on each visitor card to trigger analysis
- Modal to display GPT-4 analysis results including `risk_level`, `justification`, and `recommended_action`.
- Conditional modal CTA button ("Start Case" or "Add to Cases") based on risk level. Need to fix this so that high-risk visitors have a case auto-created.

## [Unreleased] - 2025.05.10
### Added:
- `group_by_keys()` utility function to modularize and generalize grouping. DRAGON SLAYED
- `paginate()` utility function, also modularized/generalized and decoupled from visitors-only.

### Changed:
- Refactored `stream_delivery()` to offload grouping and pagination helpers mentioned above.


## [Unreleased] - 2025.05.12
### Added:
- `class VisitorsFlagged()` table to database. Tested functionality over on /docs successfully.
- crud.py function `visitor_flag_post()` to handle db session for VisitorsFlagged table.
- app.py `"/visitor-flag"` endpoint to prepare and send data to above crud.py function.
- `flagAccount.js` for user-controlled visitor flagging & case creation.

### Changed:
- Jumped into Postgres conf file to set default timezone to `'Asia/Tokyo'`. Restarted, and good to go.