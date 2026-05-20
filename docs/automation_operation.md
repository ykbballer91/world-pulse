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

The beta uses a 30-day baseline calculation. Wikipedia 30-day backfill is reserved for initial setup and manual correction. The scheduled daily build uses a short, non-critical Wikipedia backfill window to avoid Wikimedia API rate limits; if a `429 Too Many Requests` response occurs, the build continues using existing data and records a warning.

## Schedule

The workflow runs every day at 7:00 JST.

GitHub Actions cron uses UTC, so the workflow uses:

```yaml
cron: "0 22 * * *"
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
- `public/share/world-pulse-latest.txt`

## Deployment

When Cloudflare Pages is connected to the GitHub repository, the generated-output commit is expected to trigger an automatic deployment.

## Failure Checks

Start with:

- GitHub Actions logs
- Supabase `raw_observations`
- Supabase `weirdness_scores`
- Supabase `display_log`

## Not Yet Automated

- X API auto-posting
- login
- payments
- alerts
- maps
- complex charts
- LLM summaries

World Pulse automation generates observation-based output only. It does not generate forecasts, alerts, recommendations, or advice.
