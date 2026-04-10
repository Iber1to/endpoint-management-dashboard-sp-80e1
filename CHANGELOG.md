# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Planned
- Add per-run error detail panel in `Sync Jobs` (failed blob + reason).
- Add filters in sync history (status/date/source).
- Add configurable retention policy for sync execution history.

## [1.0.0] - 2026-04-10

### Added
- Persistent sync execution history in database (`sync_runs`) with API support.
- Sync Jobs UX improvements: current run state, recent executions table, snapshot range column.
- Manual sync test mode (`force=true`) to bypass the 8h guardrail for controlled testing.
- Source deletion in Settings with safe FK handling.

### Changed
- Incremental blob ingestion based on `last_sync_at` with lookback window.
- Sync execution status now returns `partial` when file-level errors exist.
- Software endpoint matching now uses JSON content instead of filename.

### Fixed
- Docker/startup issues caused by shell entrypoint formatting and env alignment.
- Sync inconsistencies where filename/content endpoint mismatches caused avoidable failures.

