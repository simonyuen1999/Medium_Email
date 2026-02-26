# OpenCode GitHub App Notes

## Overview

When running `opencode github install` in a GitHub repository, it creates a `.github/workflows/opencode.yml` file that enables OpenCode to run as a GitHub bot.

## The Workflow File

Location: `.github/workflows/opencode.yml`

Note: I don't want this workflow, so the above file is renamed to dot-github-workflows-opencode.yml file

```yaml
name: opencode

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  opencode:
    if: |
      contains(github.event.comment.body, ' /oc') ||
      startsWith(github.event.comment.body, '/oc') ||
      contains(github.event.comment.body, ' /opencode') ||
      startsWith(github.event.comment.body, '/opencode')
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      pull-requests: read
      issues: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          persist-credentials: false

      - name: Run opencode
        uses: anomalyco/opencode/github@latest
        env:
          OPENCODE_API_KEY: ${{ secrets.OPENCODE_API_KEY }}
        with:
          model: opencode/big-pickle
```

## What It Does

- Listens for comments on PRs and issues
- Triggers when a comment contains `/oc` or `/opencode`
- Runs OpenCode on your codebase using the `anomalyco/opencode/github` action

## When It's Used

When you post a comment like `/oc fix this bug` or `/opencode refactor this` on a GitHub issue or pull request, the workflow runs and OpenCode will attempt to fix/refactor the code in your repository.

## How It Works

1. Someone comments with `/oc` or `/opencode` (plus instructions)
2. GitHub Actions triggers this workflow
3. It checks out your code and runs OpenCode with your API key
4. OpenCode makes changes and can create a PR with the fixes

---

## FAQ

### Question 1: Is OpenCode GitHub App installed per repo or for all repos?

The OpenCode GitHub App is installed **per repository** (or per organization if you install it at the organization level). You choose which repos it has access to during installation.

### Question 2: I have GITHUB_TOKEN env var defined locally AND OpenCode GitHub App installed. What does that mean?

- `GITHUB_TOKEN` in your local environment is for to the GitHub Action
 local development, unrelated- Having the OpenCode GitHub App installed means OpenCode can use the app's **installation access token** to perform GitHub operations (create branches, commits, PRs) on behalf of the app
- If you DON'T install the app, you must grant explicit permissions in the workflow and OpenCode will use the built-in `GITHUB_TOKEN` instead

### Question 3: How does OpenCode know what to do from the comment?

Yes, OpenCode reads the **entire comment body** after `/oc` or `/opencode` as the instruction. For example:
- `/oc explain this issue` → OpenCode reads the issue and explains it
- `/oc fix this bug` → OpenCode analyzes and creates a PR with the fix
- `/oc refactor this function` → OpenCode makes the changes

### Question 4: Required permissions in workflow (when NOT using OpenCode GitHub App)

When NOT using the OpenCode GitHub App, grant these permissions in your workflow:

```yaml
permissions:
  id-token: write      # Required for OpenCode to run
  contents: write     # To create branches and commits
  pull-requests: write  # To open PRs
  issues: write       # To comment on issues
```

The `id-token: write` is always required. The other permissions are only needed if you want OpenCode to make changes (not just read/analyze).

## Example Usage

- **Explain an issue**: `/opencode explain this issue`
- **Fix an issue**: `/opencode fix this`
- **Review PRs and make changes**: `Delete the attachment from S3 when the note is removed /oc`
- **Review specific code lines**: Comment on specific lines in Files tab with `/oc add error handling here`

## Appendix

Reference: https://opencode.ai/docs/github/

It shows more GitHub workflow which use OpenCode:
- schedule
- Pull Request (PR) and review
- Issue triage

And some examples to use /oc or /opencode in the comment field.
