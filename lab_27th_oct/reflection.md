# Reflection

**Q1. What did static analysis catch that careful reading alone might have missed?**

Reading the code I spotted the obvious bug in `slot_hours("14-12")` (it returns
`-2`) and the bare `except`, but I did *not* notice the mutable default argument
`equipment_list=[]` or the command-injection risk in
`os.system("cat " + file)`. The former only bites on repeated calls, and the
latter looks harmless until you realise the filename is user-controlled. Pylint
and Bandit flagged both instantly, which showed me how tools surface latent
problems that are easy to skip over when the code "looks fine".

**Q2. How do the three tools complement each other?**

Each tool has a distinct job. **Bandit** is a security guard — it found the
shell-injection (`B605`) and the silently-swallowed exception (`B110`).
**Pylint** is the strict reviewer — it caught design smells (mutable defaults,
global state, missing docstrings, non-idiomatic formatting) and scored the file
5.60/10. **Flake8** is the grammar checker — it enforced PEP 8 (blank lines,
line length, unused names). Together they cover security, design/quality and
style; a single tool would have left whole categories unchecked.

**Q3. How did I decide what to fix and in what order?**

I followed severity. First the *high*-severity Bandit findings (command
injection, bare except) because they are the most dangerous. Then the Pylint
quality issues that affect correctness and maintainability (mutable default,
global state, resource handling). Finally the Flake8 style issues, which are
cosmetic but make the code consistent and readable. Re-running all three tools
after each commit let me confirm each fix was effective and nothing regressed.

**Q4. How will I use static analysis in future work?**

I will run Pylint, Bandit and Flake8 as part of my regular workflow — ideally
in a pre-commit hook or CI step — rather than only at the end of a project. The
biggest lesson is that a clean 10.00/10 Pylint score, a zero-issue Bandit scan
and a clean Flake8 run together give a concrete, repeatable bar for "is this
code ready to share?" that a quick manual read can't match.
