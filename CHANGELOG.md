# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **[ARCH-8184]** Backend Task Priority Filtering & Bulk Completed Tasks CSV Export Engine:
  - Query parameter priority filtering (`?priority=low|medium|high`) on root route `/` with case-insensitive normalization and fallback.
  - Dedicated bulk completed task CSV export endpoint (`/tasks/completed/export` and `/export/completed/csv`) adhering to RFC 4180.
  - Protection against spreadsheet CSV injection (DDE attacks) by prefixing dangerous formula characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes.
  - 12-factor infrastructure support via `.env.example`, `.gitignore`, and `docker-compose.yml`.
  - Comprehensive pytest test suite (`tests/test_priority.py`, `tests/test_export.py`, `tests/test_security.py`).
