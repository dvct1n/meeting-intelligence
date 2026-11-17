# GitHub release and publication checklist

## Before making the repository public

- [ ] Confirm the repository owner/path is `dvct1n/meeting-intelligence` or update badges and links if the repository name differs.
- [ ] Run `make check`, `make demo` and `make synthetic-eval` from a clean virtual environment.
- [ ] Review `git status --short` and `git diff --cached` before every push.
- [ ] Run a local secret scan (`gitleaks git .`) and wait for the GitHub Security workflow to pass.
- [ ] Confirm `.env`, recordings, transcripts, model caches, Qdrant storage, private logs and exports are not tracked.
- [ ] Review all sample data and screenshots for personal or confidential information.
- [ ] Confirm the LICENSE allows the intended distribution and all sample assets are original or redistributable.
- [ ] Check that `CITATION.cff`, `CODE_OF_CONDUCT.md` and `SECURITY.md` are present and accurate.
- [ ] Update `CHANGELOG.md`, `CITATION.cff` and the version before creating a release.
- [ ] Publish only real benchmark results that can be reproduced; label fixture calculations as synthetic demonstrations.

## First push

```bash
git init
git branch -M main
git add .
git status --short
git diff --cached --stat
git diff --cached
git commit -m "chore: prepare public portfolio release"
git remote add origin https://github.com/dvct1n/meeting-intelligence.git
git push -u origin main
```

If the remote already exists, inspect it with `git remote -v` before adding or replacing it.

## If a credential or private meeting file was committed before

Ignore rules do not remove tracked files or erase Git history. Revoke/rotate any exposed credential immediately. Remove the file from the current tree and rewrite Git history where appropriate, then force-push only after coordinating with collaborators. Treat exposed credentials as compromised even after history cleanup.
