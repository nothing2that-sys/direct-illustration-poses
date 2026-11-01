# Git identity and pull requests

- Commits in this repository must use author and committer name `nothing2that-sys` and email `nothing2that@gmail.com`.
- Before committing, verify both identities with `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`. Stop if either differs; do not fall back to the machine's global identity.
- Authenticate pushes and create pull requests only as GitHub account `nothing2that-sys` (user ID `331910699`). Never fall back to another connected account.
- Configure identity per repository; do not change the user's global Git identity.
- `python setup_git.py --auto-clones` registers URL-specific global conditional includes for future clones on this PC. It must not change the global default name/email or affect unrelated repository URLs.
- `.github/workflows/owner-only-pr.yml` closes PRs opened by any other account. It must never check out or execute PR code because it runs with base-repository permissions.
- Gallery images, local reference bundles, and private absolute paths must not be committed.
