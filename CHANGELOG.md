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

## [Unreleased] - 2025.05.12
### Added:
- `/flagged-visitors` and `flagged-visitors/{case_id}` endpoints. They return a thinned out list of all cases, and the details for one specific case, respectively.
- New "Cases" section in `dashboard.html`, including a sidebar navigation link and a `.case-listout` table.
- `fetchCaseLoad.js` module to dynamically populate the cases table from the backend API.

### Changed:
- `class VisitorsFlagged()` has been split into `class VisitorsFlaggedSummary()`, which returns an info-light list of all cases, and `class VisitorsFlagged()` which builds on top of `VisitorsFlaggedSummary()`, and is used for full case detail retrieval, as well as new case creation (still). Functional testing still successful.

## [Unreleased] -  2025.05.17
### Added:
- `caseModal.js` Case Modal added with a "Suspend Account" action button, and Abuse IPDB information dropdown.

## [Unreleased] -  2025.05.19
### Added:
- Implemented `vps_login_monitor.sh` script to SSH into the VPS, parse recent failed SSH login attempts, and print structured CSV output (timestamp, IP, username, message).
- Created a `FailedLoginIntel` table to collect details on repeat-offender ip addresses, and ultimately hand off to AI for further analysis.

## [Unreleased] -  2025.05.21
### Added:
- `crud.py` function `upsert_failed_login_attempt()` to batch process failed login lines per IP, checking for existing rows and appending attempts. State managed to prevent duplicate writes and needless requests.

### Changed:
- AbuseIPDB enrichment implemented using `ipabuse_check()` in new `services.py` file (function moved from `utils.py`).
- Migrated AI analysis `analyze_user()` to `services.py` and removed `visitor_analysis.py`
- Server-level ssh config file settings altered to permit login via key only: `PasswordAuthentication no`, `ChallengeResponseAuthentication no`, `UsePAM no`.