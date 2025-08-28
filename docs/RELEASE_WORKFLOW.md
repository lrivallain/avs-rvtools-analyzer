# Release Workflow Guide

This document explains the release workflow for the AVS RVTools Analyzer project.

## Overview

The project uses a simple, automated release workflow designed for a single maintainer with minimal overhead while following best practices.

## Versioning

- **Pattern**: CalVer (Calendar Versioning) - `YYYY.M.PATCH`
- **Example**: `2025.8.6` (Year 2025, Month 8, Patch 6)

## Branch Strategy

- **`master`**: Main development and stable branch
- **Feature branches**: `feat/feature-name`, `fix/bug-name` (short-lived)

### Workflow
1. Create feature branch from `master`
2. Develop and commit changes
3. Create Pull Request to `master`
4. Tests must pass before merge
5. Merge to `master`
6. When ready to release, create a tag

## Release Process

```bash
# 1. Ensure you're on master and up to date
git checkout master
git pull origin master

# 2. Update version in pyproject.toml
uv bump patch
# or
uv bump minor
# or
uv bump major

# 3. Commit version bump
git add pyproject.toml
git commit -m "bump: version 2025.8.6"

# 4. Create and push tag
git tag -a 2025.8.6 -m "Release 2025.8.6"
git push
git push --tags
```

## What Happens After Tagging

When you push a tag matching `20*.*.*`:

1. **Tests run** on the tagged commit
2. **Version validation** ensures tag matches pyproject.toml
3. **PyPI publishing** happens automatically
4. **GitHub Release** is created with:
   - Auto-generated changelog
   - Commit history since last release
   - Merged pull requests

## GitHub Actions Workflows

### `test.yaml`
- Runs tests on all pushes and PRs
- Clean workflow - only shows relevant jobs for PRs

### `release.yaml`
- Only triggered by version tags (no ignored jobs in PRs)
- Runs tests, publishes to PyPI, and creates GitHub releases

### `pr-checks.yaml`
- Additional quality checks for PRs
- Code coverage reporting
- Optional linting and formatting checks
- PR title validation (conventional commits)

## Best Practices

### For Development:
- Use conventional commit messages (`feat:`, `fix:`, `docs:`, etc.)
- Create PRs for all changes
- Keep feature branches small and focused
- Write tests for new features

### For Releases:
- Release frequently (every few features/fixes)
- Review the generated GitHub release notes
- Monitor the Actions tab for any failures

## Troubleshooting

### Tests Failing
- All tests must pass before release
- Fix issues and re-tag if necessary
- Use `git tag -d VERSION` and `git push origin :refs/tags/VERSION` to delete bad tags