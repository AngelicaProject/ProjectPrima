# Discord release announcements

`discord-release.yml` announces published `harmonia/` releases automatically.
The existing Aeria/Harmonia publishing process is unchanged. The webhook URL
is stored only in the Actions secret `DISCORD_WEBHOOK_URL`.

The card lists commit subjects since the previous published release in the
same channel (stable or prerelease). Only actual merge commits (more than one
parent) are omitted. All other commits are included, with or without a naming
convention, including `ci/build/chore/test/docs`. Repeated subjects are combined,
and at most ten subjects are shown with a link to the full comparison.
The card includes a short note that Harmonia updates the translation automatically.
The summaries quote commit subjects; they do not infer counts of proofread
strings, include internal commit bodies, or require manually written release notes.

The workflow runs only when a release is published, not when its metadata is
edited. It does not rewrite GitHub release descriptions. A workflow rerun or
a manual send posts another message, so use the default dry-run option for previews.

To preview an existing release, run the workflow manually with its full tag
and `dry_run=true`. Set `dry_run=false` to announce it to the configured channel.
The URL must be a regular Discord webhook URL without `/github` at the end.

Tests: `python -m unittest discover -s .github/scripts -p 'test_*.py'`.
