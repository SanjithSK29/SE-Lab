# Issues Found & Fixed — `scheduler_system.py`

Static analysis was run against the original file with Pylint (5.60/10),
Bandit (1 high + 1 low) and Flake8 (13 violations). The table below documents
the issues in priority order (high/medium first) and how each was resolved.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Shell command injection via `os.system("cat " + file)` | Security (Bandit B605) | 43 | `file` is concatenated into a shell command, so a malicious filename could execute arbitrary commands. | Removed the shell call entirely. Conflicts are now written with `open(...)` and printed to stdout directly — no subprocess/shell. |
| Bare `except:` with `pass` | Bug / Security (Bandit B110, Flake8 E722) | 27 | Catches *every* exception (including `KeyboardInterrupt`) and silently swallows it, hiding real errors. | Replaced with a specific `except KeyError:` that returns early, so only "missing reservation" is handled. |
| Mutable default argument `equipment_list=[]` | Bug (Pylint W0102) | 11 | The same list object is shared across all calls, so equipment from one booking leaks into the next. | Changed default to `None` and initialised a fresh list inside the function. |
| Unbounded module-level global state + `global` statement | Design (Pylint W0603, C0103) | 9–12 | Mutable globals (`reservations`, `next_reservation`, …) and the `global` statement make the code hard to reason about and reuse. | Encapsulated all state in a `Scheduler` class with instance attributes; removed every `global`. |
| `open()` without `with` and without `encoding` | Resource / Quality (Pylint W1514, R1732) | 35, 40 | Files were never closed and the encoding was platform-dependent. | Used `with open(..., "w", encoding="utf-8")` context managers everywhere. |
| Non-snake-case function name `logConflicts` | Style (Pylint C0103) | 39 | Violates PEP 8 naming convention. | Renamed to `log_conflicts`. |
| Missing module & function docstrings | Quality (Pylint C0114, C0116) | 1, 11, 22, 30, 34, 39, 45 | No documentation describing intent. | Added a module docstring and a docstring for every class and method. |
| String formatting with `%` and concatenation | Quality (Pylint C0209, C0206) | 15 | Outdated `%` formatting; looped over dict keys instead of values. | Switched to f-strings and iterated with `.values()`. |
| Unused variables `a`, `a_more`, `c` | Quality (Pylint W0612, Flake8 F841) | 46, 47, 49 | Results of `schedule_room` were assigned but never used. | Removed the unused assignments; kept only the booking id that is actually read. |
| Lines over the character limit | Style (Flake8 E501) | 14, 18 | Lines exceeded 79 characters. | Wrapped long statements and f-strings onto multiple lines. |
| Missing blank lines around functions | Style (Flake8 E302, E305) | 11, 22, 30, 34, 39, 45, 59 | Inconsistent spacing made the file harder to scan. | Added the required two blank lines between top-level definitions. |
| Wrong runtime output (found by manual inspection) | Logic bug | 48, 49 | `slot_hours("14-12")` returns `-2` (end before start), and `"Huddle-3"` was booked with an `int` `1530` instead of a time string. | Corrected the demo slots to valid, ordered strings (`"12-14"`, `"15-16"`). |

## Results after the fixes

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.60 / 10 | **10.00 / 10** |
| Bandit | 1 High + 1 Low issue | **No issues** |
| Flake8 | 13 violations | **Clean (exit 0)** |
