# Engineering Standards & Code Review Guidelines

## PR & Code Review Workflow
1. Branch from `main` using standard prefixes: `feat/`, `fix/`, `docs/`, `refactor/`.
2. Ensure automated linters pass: `flake8 src tests`.
3. All PRs require at least one peer code review before merging into `main`.
4. Ensure 100% pass rate on test harness: `pytest tests/ -v`.
