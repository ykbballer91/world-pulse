# World Pulse Automation Operation

World Pulse can run as a daily GitHub Actions workflow. The workflow generates the daily display JSON, share image, and X post text, then commits those generated files back to GitHub.

## Flow

1. GitHub Actions checks out the repository.
2. Python is installed.
3. Dependencies are installed from `requirements.txt`.
4. `DATABASE_URL` is loaded from GitHub repository secrets.
5. `scripts/run_daily_world_pulse.py` runs the daily build.
6. The workflow verifies generated files exist.
7. If generated files changed, GitHub Actions commits and pushes them.
8. If Cloudflare Pages is connected to the GitHub repository, that commit is expected to trigger deployment.

The beta uses a 30-day baseline calculation. Wikipedia 30-day backfill is reserved for initial setup and manual correction. The scheduled daily build uses a short, non-critical Wikipedia backfill window to avoid Wikimedia API rate limits; if a `429 Too Many Requests` response occurs, the build continues using existing data and records a non-critical note.

Normal daily builds normalize only the recent scoring window, with a small buffer beyond the 30-day baseline. Full normalization across all raw observations should be run manually after major backfills or validation work. Long-range validation jobs such as 90-day or 1-year reviews should stay outside the scheduled daily workflow.

90-day backfill is a manual validation workflow for Reality-Reflection examples and is not scheduled in GitHub Actions. USGS can be requested as a 90-day M4+ window. NOAA SWPC is constrained by the provider's current Kp and X-ray response windows, so the helper verifies those current responses rather than replaying a full 90-day history. Wikipedia 90-day backfill should be run in stages to reduce Wikimedia API rate-limit pressure; failed dates are logged for later retry.

Sources are also classified internally into `reality`, `attention`, and `context` layers for future Reality-Reflection Gap analysis. These layers are not exposed in the public UI; the public label remains Signal Position, and gap scores are not published. The stored database label `attention` is retained for backward compatibility: Wikipedia Pageviews is treated as a delayed reflection / interpretation proxy, not immediate human attention. An immediate human-attention stream is not implemented yet.

## Public Snapshot Policy

Daily public snapshots use UTC yesterday by default. The data date is not the posting date.

Dated share files are intended to be the public archive for that data date:

- `public/share/world-pulse-YYYY-MM-DD.txt`
- `public/share/world-pulse-YYYY-MM-DD.png`
- `public/share/world-pulse-YYYY-MM-DD.jpg`

Latest files are moving pointers to the latest generated snapshot:

- `public/display/latest.json`
- `public/share/world-pulse-latest.txt`
- `public/share/world-pulse-latest.png`
- `public/share/world-pulse-latest.jpg`

Backfill or recalculation may change internal scores, but public snapshots should not be casually overwritten after posting. If a published snapshot must be corrected, document the correction explicitly.

## Schedule

The workflow runs every day at 09:30 JST.

GitHub Actions cron uses UTC, so the workflow uses:

```yaml
cron: "30 0 * * *"
```

## GitHub Secret

Add this required GitHub repository secret:

```text
DATABASE_URL
```

Use the Supabase connection string for `DATABASE_URL`.

Optionally add this GitHub repository secret for Cloudflare Radar ingestion:

```text
CLOUDFLARE_API_TOKEN
```

`CLOUDFLARE_API_TOKEN` is optional initially. If it is not set, Cloudflare Radar ingestion is skipped without stopping the daily build.

Setup path:

1. Open the GitHub repository.
2. Go to Settings.
3. Go to Secrets and variables.
4. Open Actions.
5. Add a new repository secret named `DATABASE_URL`.
6. Paste the Supabase connection string.
7. Optionally add `CLOUDFLARE_API_TOKEN`.

## Manual Run

Use:

```text
GitHub Actions -> Daily World Pulse -> Run workflow
```

## Generated Files

- `public/display/latest.json`
- `public/share/world-pulse-latest.png`
- `public/share/world-pulse-latest.jpg`
- `public/share/world-pulse-latest.txt`
- `public/share/world-pulse-YYYY-MM-DD.png`
- `public/share/world-pulse-YYYY-MM-DD.jpg`
- `public/share/world-pulse-YYYY-MM-DD.txt`

## Deployment

When Cloudflare Pages is connected to the GitHub repository, the generated-output commit is expected to trigger an automatic deployment.

## Failure Checks

Start with:

- GitHub Actions logs
- Supabase `raw_observations`
- Supabase `weirdness_scores`
- Supabase `display_log`

## X Posting Dry Run

X posting is currently manual. `scripts/post_to_x.py` validates the current generated text and image without making X API calls. Live X API posting is not enabled yet.

Do not add credentials to the repository. Do not enable live posting until API access, cost, and duplicate prevention are confirmed.

## Not Yet Automated

- X API auto-posting
- login
- payments
- notifications
- maps
- complex charts
- LLM summaries

World Pulse automation generates observation-based output only. It does not generate forecasts, notifications, recommendations, or advice.
