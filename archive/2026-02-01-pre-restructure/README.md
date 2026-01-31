# Archived: src/ Package (Pre-Restructure)

**Archived Date:** 2026-02-01
**Reason:** Superseded by genie/ package structure
**Commit Reference:** 2112948 (refactor: Restructure project with app/ directory and genie package)

## Context

This directory contains the old `src/` package structure that was renamed to `genie/`
in commit 2112948. The src/ directory only contained __pycache__ files at the time
of archival (no active source code).

## Migration Path

- Old: `from src.api import GenieSpaceClient`
- New: `from genie.api import GenieSpaceClient`

All imports and documentation have been updated to use the genie/ package.
