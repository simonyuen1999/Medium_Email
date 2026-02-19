# GitHub Workflow Note

GitHub blocks pushes that add/modify workflow files unless your credentials/token have the Actions/workflow permission. Fix by creating a token with the workflow permission (or use the web UI / GH CLI / org-owner changes). Steps below.

* Create a token that can update workflows (recommended: fine‑grained PAT)
  1. On github.com click your avatar → Settings → Developer settings → Personal access tokens → Generate new token → Fine‑grained token.
  2. Select the target repository under "Repository access".
  3. Under "Permissions" set:
     * Code / Contents: Read & write
     * Workflows (or Actions/Workflows): Read & write (or "update" if shown)
  4. Generate token and copy it (store securely).
  5. Use the token for git HTTPS pushes (credential helper or [gh auth login](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) recommended).
* Or use a classic PAT (less recommended): Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token and include the `workflow` scope plus `repo` as needed.
* Example quick test push (avoid embedding token in repo URL permanently):
  * Temporarily set remote with token (do NOT check this into files):
    * `git remote set-url origin https://USERNAME:PERSONAL_ACCESS_TOKEN@github.com/OWNER/REPO.git`
    * [git push origin main](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html)
  * Better: run `gh auth login --web` to let GitHub CLI authenticate your local git credential helper with appropriate scopes.
* If this is an organization repo
  * Org policies can further restrict who can create/modify workflows. If a token still fails, an org owner may need to:
    * Grant your account permission to modify workflows, or
    * Allow workflow updates from tokens/CI, or
    * Approve your PAT scopes.
  * Check: Organization → Settings → Actions → Policies.
* Alternatives if you don’t want to create a PAT with workflow scope
  * Create or edit the workflow directly on GitHub.com (Repository → Add file → Create new file) — web UI commits do not require a PAT.
  * Open a branch and create a pull request; a maintainer with sufficient rights can merge.
  * Use a self-hosted runner approach (not relevant to the push permission), or have an admin run the push for you.
* Security tips
  * Do not print secrets or tokens in logs.
  * Use fine‑grained tokens with minimal repo access and an expiry.
  * Prefer [gh auth login](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) instead of embedding PATs in URLs.

### Appendix

I cannot push the commit with `.github/workflow/mcp_run.yml` file with my original token.

Then, I created a new Token for this repo

`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`

I can use this command to push the commit.

`git remote set-url origin https://simonyuen1999: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@github.com/simonyuen1999/Medium_Email.git`<hr>

## Schedule task?

The mcp\_run.yml has `schedule and cron` setup. Will this workflow automateically be executed? Or, it can only be triggered by GitHub Actions?

Short answer: the schedule in [mcp\_run.yml](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) is executed automatically by GitHub Actions on GitHub’s runners according to the cron you set — no local process required. Because you also included `workflow_dispatch`, the same workflow can also be started manually from GitHub’s Actions UI.

Key points to know (concise):

* Automatic vs manual
  * **schedule/cron:** GitHub runs it automatically on schedule (times are UTC).
  * **workflow\_dispatch**: lets you manually start it from the repository → Actions → MCP Run → Run workflow.
  * **Both can coexist;** each trigger will start the same workflow.
* Where it runs
  * Runs on GitHub-hosted runners when `runs-on: ubuntu-latest` is used. GitHub provisions the VM and executes your job.
  * If you switch to a self-hosted runner, that runner must be online for scheduled/manual runs to execute there.
* Requirements for automatic scheduled runs to work
  * Actions must be enabled for the repository (Repository → Settings → Actions).
  * The repo must not be archived.
  * The workflow file must be in the default branch (cron jobs run against the default branch unless configured otherwise).
  * If the workflow uses secrets, add them in Settings → Secrets and variables → Actions.
* Security / behavior notes
  * Scheduled workflows run on GitHub infrastructure and can access repository secrets injected into the runner (so your adapter can read `GMAIL_USERNAME`/`GMAIL_PASSWORD` from env when the workflow runs).
  * Scheduled workflows do not run for fork repositories in the same way (and secrets are not exposed to untrusted PRs).
  * Billing: GitHub-hosted runner minutes and artifact storage are charged per your plan (public repos are broadly free; private repos have an included allotment then bill).
* How to verify
  * After pushing the workflow, check the Actions tab for runs (manual or scheduled). The run list and logs show execution and artifacts.

## Re-run the workflow

1. After committed any change into `.github/workflow/*.yml` file(s), make sure your GitHub access token has Workflow R/W permission.
2. The best way is to visit the repo and see the latest content in the current version.
3. Do not just re-run the existing Workflow since it still use the old commit hash.
4. Always start with a new Actions > Show all existing workflow.
5. In this project,
   1. The workflow is `MCP Run`
   2. The description: This workflow has a `workflow_dispatch` even trigger.
6. Click the `Run workflow`, pick the branch, and click the Run.

At the end of the `mcp_run.yml `workflow file, it try to check-in the output files to git branch, but these commands are commented out.   We keep them for documentation.
