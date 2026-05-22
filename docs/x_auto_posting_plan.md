# X Auto Posting Plan

## Purpose

Automatically publish the generated World Pulse daily text and share image after a successful daily build.

## Source Files

- `public/share/world-pulse-latest.txt`
- `public/share/world-pulse-latest.jpg`

## Posting Policy

- Post only after daily build success.
- Post only once per data date.
- Use Data date, not local posting date.
- Do not post if the text file is missing.
- Do not post if the image file is missing.
- Do not post if the image file size is zero.
- Do not post if the data date cannot be parsed.
- Do not post if text contains blocked wording.
- Keep dry-run mode permanently available.

## Required X Credentials

Likely environment variables:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

OAuth2 user-token based posting may be used depending on the final API implementation.

Secrets must never be committed to the repository or printed in logs.

## Cost Note

X API access may require paid access or usage credits. Posts containing URLs may be treated differently from plain text posts. Final cost and access details must be checked in the X Developer Portal before live posting.

Do not hardcode exact pricing in the repository.

## Failure Policy

- If media upload fails, do not create the post.
- If post creation fails, fail the script.
- Never log secrets.
- Log enough non-sensitive information for debugging.

## Duplicate Prevention

Initial local dry-run approach:

- Use a local JSON log file such as `.x_posted_dates.json`.
- The log should not be committed by default.
- It records `data_date` and optional `post_id` after live posting is implemented.

Future production approach:

- GitHub Actions artifact, private state store, or small database table.
- Do not use `public/share` as the source of posting state.

## Live Posting Is Not Enabled Yet

Current phase is dry-run only.

- No X API calls are made.
- Live posting requires separate approval.
- GitHub Actions should not include a live posting step until credentials, cost, and duplicate prevention are confirmed.
