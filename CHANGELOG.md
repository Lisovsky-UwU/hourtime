# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.5.1] - 2026-10-21

### Fixed

- Devices kept signing each other out. A refresh with a token revoked by
  logout or a bulk revoke was taken for a stolen token and revoked every
  session of the user, so each signed-out device signed out the rest on its
  next refresh. Only a token already replaced by a refresh counts as stolen now.
- Tabs of one browser pick up tokens refreshed or cleared in another tab
  instead of replaying a stale refresh token.

## [0.5.0] - 2026-10-20

### Added

- Shared workspaces. An admin invites people with a one-time link that lasts 7
  days and can be revoked; the link also signs up a new account when open
  registration is off. The Members page lists everyone with their role: admins
  promote, demote and remove members, anyone but the owner can leave.
- Roles: members create projects, clients and tags; changing or deleting them,
  and the workspace name, rate and currency, is for admins.
- Workspace switcher in the sidebar, with "Create workspace". The choice is
  kept in the profile, so the next load and new tabs open the same workspace.
- Team reports: a member filter, grouping by member and a member column in the
  detailed report and its CSV, shown once a workspace has more than one person.
  The timer, calendar and timesheet still show only your own entries.

### Changed

- The API takes the workspace in the path: `/workspaces/{id}/projects` and so
  on. The running timer is per user: `/me/time-entries/current` and
  `/me/time-entries/{id}/stop`.
- Personal workspaces are named after the owner's email instead of "Personal".

## [0.4.0] - 2026-10-14

### Added

- Timesheet: a week as a table of rows by project, client or project and
  description, one column per day. Type a new total into a cell: more time adds
  an entry for the difference after the day's last entry, less time trims the
  latest entries (deleting any asks first). Rows by client are read-only. The
  week is picked on a month calendar that marks it.
- Calendar zoom: "Zoom out" and "Zoom in" switch the hour height between 48,
  72, 96 and 144 px; the choice is remembered in the browser.
- The timer bar is on the calendar page too, so a timer can be started and
  stopped without leaving it.

### Changed

- The calendar takes the full page width, and entry blocks fit their text to
  their height.
- Reports: a custom period is picked on one range calendar (first click - the
  start, second - the end) and applies at once; the weekly report picks its
  week on a month calendar.

## [0.3.0] - 2026-10-10

### Added

- Calendar: a week and a day grid of your entries. Drag a block to move it,
  stretch it to change the duration, draw on an empty slot to create an entry,
  and click a block to edit it in place. Entries across midnight show in two
  parts; day totals count by the start day.
- Report export: summary and detailed reports as CSV (comma-separated, UTF-8,
  opens in Excel as values), and a print layout for printing or saving as PDF.

### Changed

- Color and date pickers are rebuilt on reka-ui: a date can be typed segment by
  segment or picked from a calendar that starts on your week start day, and a
  custom project color has a proper color area, hue slider and hex field.

[0.4.0]: https://github.com/Lisovsky-UwU/hourtime/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Lisovsky-UwU/hourtime/compare/v0.2.0...v0.3.0
