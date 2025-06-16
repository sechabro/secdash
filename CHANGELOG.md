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



## [Unreleased] - 2025.05.23
### Added:
- `ip_analysis_gathering() -> analyze_ip_address()` AI analysis workflow added to `services.py`. Dragon note regarding asyncio.gather() scaleability added, but for current purposes, works very well as-is.
- `FailedLoginInMem` dataclass added for faster handling of IP address intel handling during analysis. 
- `/ban-ip` endpoint added for manual ip bans.

### Changed:
- `block_ip()` is now `ip_to_blacklist()` in `utils.py`.



## [Unreleased] - 2025.05.24
### Added:
- Implemented `get_unanalyzed_ips() -> ai_analysis_update()` crud flow. A GET to the database returns all rows missing AI analysis. They're sent over to `services.py` to be processed/analyzed by `ip_analysis_gathering()` flow. Then each row is updated with the appropriate GPT-based analysis.
- This repeating flow has been added as an asyncio task in `async def on_startup()`, and canceled in `async def shutdown_async()`

### Changed:
- Restructured the `ActionType` enum class to streamline values with permitted values from AI analysis.
- Appended two additional columns to the `FieldLoginIntel` table - `status` and `status_change_date`. `status` pulls from a `CurrentStatus` enum class, and displays the current status of the IP address (active, suspended, or banned). `status_change_date` is a datetime object that will be changed in tandem with a change in `status` value. This will allow for a suspended account cooldown timer in the future.

### Fixed:
- The return object from Abuse IPDB is shaped like `{"data":{<data in here>}}`, thus all `.get()` calls to the object were returning `None`, as they were not structured correctly. Altered the return value in `ipabuse_check()` and all calls are working as expected, once again.

## [Unreleased] - 2025.05.27
### Added:
- `/get-ips` and `/ban-ip` endpoints to allow a GET for populating frontend, and a user-controlled ip address ban feature.
- Implemented `get_all_ips()` in `crud.py` to populate frontend.
- `FailedLoginIPBan` pydantic model added for ip bans & reinstatements.
- Built a modular `ip_status_update` to account for status updates implemented from the frontend, outside of the automation loop. `FailedLoginBan` is used here.

### Changed:
- Moved `ip_to_blacklist()` from `utils.py` to a new `ipset.py` to avoid a circular import trap. Function has also been renamed to `ipset_calls()` as it handles both blacklisting and whitelisting functionality.

## [version 1.0.0] - 2025.05.31
### Added:
- Mounted a `styles` folder and created `dashboard.css` inside.
- Created a `countryMapping.js` to contain references of country codes and their respective country names.
- Connected `/ip-stream` event to frontend via `fetchIPS.js`.
- Connected `/ipset-calling` POST to frontend via `iPSetCall.js`.
- Mapped country codes, country names, and ssh attempt counts to world map using `mapEChart.js` module.
- Created `mapModal.js` module to populate a modal with relevant ip data when a country is clicked on the map.


### Changed:
- All `.sh` in /scripts revised to include a prod-environment-native version. Local version commented out.
- `ABPWD` env var now loaded via dotenv.
- `ipset_calls` now with prod-environment-native cmd variable. Logging statements changed to reflect correct wording.
- Removed several unnecessary pip packages used for faking user data. Update reflected in `requirements.txt`.
- Removed or disabled all user data implementation. Too heavy, and not very useful. Will reapproach when there are actual site data to tie into.
- Revised `FailedLoginInMem` schema to also include a recommended action value, `reco_action`.
- Restructured `new_snapshot` in `ip_stream_delivery` to serialize by default using `[asdict(ip) for ip in ips]`, to assist with frontend data refresh.
- Included an auto-refresh at `/ipset-calling` to force an update to `ips` deque object, in order to reflect an immediate frontend data update after a ban or restore takes place on an ip address.
- Altered querySelector for `const tableBody` in `fetchConnectionsdata.js`.
- Removed now-unusable chart objects from `ioChart.js`. Changes also reflected in `iostatStreamHandler.js`.
- Removed `visitors` tab from `uiHandlers.js`, and replaced it with an `ip-panel-section` tab instead.
- Switched all frontend Japanese over to English.

### Fixed:
- In `ip_status_update`, changed incorrect `current_status` column name to correct `status` naming convention, to match FailedLoginIntel schema.


## [version 1.0.1] - 2025.06.16
### Added:
- Introduced SSE-based in-app alert delivery for live security notifications at `/alert-stream`. Includes AI-driven risk analysis alerts, autoban actions. Notified via toast alerts, with expandable content in message center.
- Integrated Alembic for ease of db-related schema updates.