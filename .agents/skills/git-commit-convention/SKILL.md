---
name: git-commit-convention
description: Use when drafting, reviewing, or generating git commit messages, branch names, and changelog updates to strictly enforce Conventional Commits standards
---

# Git Commit Convention

## Overview
All commit messages must follow the **Conventional Commits 1.0.0** specification. Clear, structured commit messages improve git log readability, enable automated changelog generation, and communicate clear intent to teammates.

---

## Commit Message Format

```text
<type>(<optional-scope>): <imperative short description>

[optional body: explain WHAT changed and WHY, not HOW]

[optional footer(s): references issue numbers or breaking changes]
```

---

## Allowed Types

| Type | When to Use | Example |
|---|---|---|
| `feat` | Adds a new feature or functionality | `feat(auth): implement JWT refresh token rotation` |
| `fix` | Fixes a bug or erroneous behavior | `fix(screener): resolve division by zero on PE calculation` |
| `refactor`| Code change that neither fixes a bug nor adds a feature | `refactor(postgres): split large query file into modules` |
| `perf` | Code change that improves performance | `perf(cache): add in-memory bloom filter for tickers` |
| `test` | Adding missing tests or correcting existing tests | `test(signal): add edge case tests for negative momentum` |
| `docs` | Documentation only changes | `docs(readme): add docker-compose setup instructions` |
| `chore` | Build process, auxiliary tools, or dependency updates | `chore(deps): upgrade pgx to v5.5.3` |
| `ci` | CI configuration files and scripts | `ci(github): add golangci-lint workflow` |

---

## The Golden Rules

1. **Imperative Mood**: Use imperative verbs in the subject line (*"add"*, not *"added"* or *"adds"*).
2. **Lowercase Subject**: Start the subject description with a lowercase letter (unless it's a proper noun/symbol).
3. **No Trailing Period**: Do NOT put a period at the end of the subject line.
4. **50/72 Rule**: Keep the subject line under 50-72 characters. Wrap the body at 72 characters.
5. **Scope Naming**: Scope should be the module, package, or domain being touched (e.g. `domain`, `stock`, `api`, `db`).
6. **Breaking Changes**: Append `!` after type/scope or include `BREAKING CHANGE:` in the footer:
   - `feat(api)!: remove deprecated v1 stock endpoints`

---

## Good vs Bad Examples

```text
❌ BAD: fixed a bug in stock calculation
✅ GOOD: fix(signal): prevent nil pointer on empty historical prices

❌ BAD: Added new Sectors API client and some models.
✅ GOOD: feat(sectors): add client for quarterly financial ratios

❌ BAD: refactor: Cleaned up code.
✅ GOOD: refactor(usecase): extract ranking logic into pure domain helper
```

---

## Pre-Commit Verification Checklist

- [ ] Does the commit message start with a valid type (`feat`, `fix`, etc.)?
- [ ] Is the scope enclosed in parentheses and relevant to the directory/module?
- [ ] Is the subject line written in the imperative mood (*"implement"*, not *"implemented"*)?
- [ ] Is there no period at the end of the first line?
- [ ] Are breaking changes explicitly marked with `!` or `BREAKING CHANGE:`?
