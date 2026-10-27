# Lab 5 Report — Static Code Analysis of `scheduler_system.py`

## 1. Overview

The goal of this lab was to improve the quality, security and style of the
provided conference-room scheduler using three static analysis tools — **Pylint**
(quality/logic), **Bandit** (security) and **Flake8** (PEP 8 style) — and to fix
at least four of the issues they reported.

## 2. Method

1. Ran the program and inspected its (wrong) output by hand.
2. Generated baseline reports for all three tools.
3. Documented the findings in `issues.md`.
4. Fixed the issues in three focused commits — one per tool:
   - `fix(bandit)`: removed the shell-injection and the bare `except`.
   - `fix(pylint)`: refactored globals into a `Scheduler` class, added
     docstrings, fixed the mutable default argument, naming and f-strings.
   - `fix(flake8)`: wrapped long lines and normalised blank lines.
5. Re-ran the tools to confirm the issues were gone and the program still works.

## 3. Before / After

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.60 / 10 | **10.00 / 10** |
| Bandit | 2 issues (1 High, 1 Low) | **No issues** |
| Flake8 | 13 violations | **Clean (exit 0)** |

Full reports are in `before/` and `after/`.

## 4. Key fixes

- **Security:** removed `os.system("cat " + file)` (command injection) and the
  bare `except:` that swallowed all errors.
- **Correctness:** fixed the mutable default argument and two invalid demo time
  slots (`"14-12"` → `"12-14"`, `1530` → `"15-16"`).
- **Design/quality:** encapsulated module globals in a `Scheduler` class, added
  docstrings, used context managers with explicit `utf-8` encoding, f-strings
  and `.values()` iteration, and removed unused variables.
- **Style:** renamed `logConflicts` → `log_conflicts`, wrapped lines to ≤79
  characters and added the required blank lines.

## 5. Conclusion

The program produces correct output after the fixes (`Slot length for b: 2`,
double-bookings are logged and the schedule exports to `schedule.json`), and all
three static analysis tools now pass cleanly. This demonstrates the value of
running static analysis continuously rather than relying on manual review alone.

See `issues.md` for the full issue table and `reflection.md` for the reflection
questions.
