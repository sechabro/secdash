# Changelog Begins

## [0.0.1] - 2025-05-03

### Added:
- Visitor.ipdb was a major memory hog. Created a `@dataclass(slots=True)` version called VisitorInMem. Reduced memory usage from 2.65mb to 0.67mb
- Implemented `get_field_value()` and `serialize()` helper functions for the universal `stream_delivery()` function, now that we are streaming both dict-based data, and dataclass formats. This required a small change to `stream_delivery()` as well.
- Integrated memory reporting log into `visitor_activity_gen()` to measure and report total usage in MB and by field. Currently commented out.

