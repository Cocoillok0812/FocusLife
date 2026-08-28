# FocusLife Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Upgrade the existing desktop task starter into a tested FocusLife self-discipline dashboard.

**Architecture:** Keep Tkinter and local JSON, separate domain calculations in `task_core.py` from navigation and rendering in `app.py`. Migrate legacy payloads at the storage boundary.

**Tech Stack:** Python 3.10+, Tkinter, unittest, PyInstaller.

## Global Constraints
- Preserve the current priority, two-minute action, timer and local-storage behavior.
- Do not commit credentials or runtime user data.

### Task 1: Domain model and migration
- [ ] Write failing tests for habits, reviews, focus sessions, debt, energy score and legacy migration.
- [ ] Run tests and confirm expected failures.
- [ ] Implement typed dataclasses and pure calculations.
- [ ] Run all tests.

### Task 2: Today dashboard and navigation
- [ ] Add Today/Habits/Calendar/Review/Data navigation.
- [ ] Enforce the three-task limit in the UI.
- [ ] Add 2/25/45/60-minute focus controls and session recording.

### Task 3: Habit, calendar, review and analytics views
- [ ] Add habit creation and idempotent daily check-in.
- [ ] Render monthly task completion calendar.
- [ ] Save nightly three-question review.
- [ ] Render weekly summaries and energy score.

### Task 4: Packaging, security and release
- [ ] Add README, launcher, `.gitignore`, requirements and build script.
- [ ] Run tests, compile check and packaging smoke test.
- [ ] Scan ZIP/repository for credentials and local data.
- [ ] Commit and push to a private GitHub repository.

