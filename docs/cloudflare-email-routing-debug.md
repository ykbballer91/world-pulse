# Cloudflare Email Routing Debug: harmonia-community.com

## Scope

This document is for diagnosing why messages to `info@harmonia-community.com` may not be forwarded to `ykbballer91@gmail.com` through Cloudflare Email Routing.

No DNS or Cloudflare settings should be changed during this diagnostic pass.

## Current DNS Findings

Commands run on 2026-05-13 JST:

```sh
dig MX harmonia-community.com
dig TXT harmonia-community.com
dig TXT _dmarc.harmonia-community.com
```

Observed result:

| Record | Current value | Notes |
| --- | --- | --- |
| `MX harmonia-community.com` | `1 smtp.google.com.` | This does not point to Cloudflare Email Routing MX hosts. |
| `TXT harmonia-community.com` | `google-site-verification=...` | Google site verification is present. |
| `TXT harmonia-community.com` | `v=spf1 include:_spf.google.com ~all` | SPF authorizes Google, not Cloudflare Email Routing forwarding. |
| `TXT _dmarc.harmonia-community.com` | `v=DMARC1; p=none; rua=mailto:postmaster@harmonia-community.com` | DMARC is monitor-only. |

Cloudflare Email Routing normally expects apex MX records routing inbound mail to Cloudflare mail exchangers:

```txt
route1.mx.cloudflare.net
route2.mx.cloudflare.net
route3.mx.cloudflare.net
```

It also normally expects SPF to include Cloudflare forwarding, commonly:

```txt
v=spf1 include:_spf.mx.cloudflare.net ~all
```

If Google mail hosting is intentionally used, SPF may need both providers in one SPF record, for example:

```txt
v=spf1 include:_spf.google.com include:_spf.mx.cloudflare.net ~all
```

Do not apply this change without confirming the intended mail architecture, because MX changes affect all inbound mail for the domain.

Reference:

- Cloudflare Email Routing setup docs: https://developers.cloudflare.com/email-routing/get-started/enable-email-routing/
- Cloudflare Email Routing DNS records: https://developers.cloudflare.com/email-routing/setup/email-routing-dns-records/
- Cloudflare Email Routing API: https://developers.cloudflare.com/api/resources/email_routing/

## Re-run DNS Checks

Use:

```sh
./scripts/check-email-routing-dns.sh
```

Or manually:

```sh
dig MX harmonia-community.com
dig TXT harmonia-community.com
dig TXT _dmarc.harmonia-community.com
nslookup -type=MX harmonia-community.com
nslookup -type=TXT harmonia-community.com
nslookup -type=TXT _dmarc.harmonia-community.com
```

## Cloudflare API Checks

If a read-only Cloudflare API token is available:

```sh
CF_API_TOKEN=... ./scripts/check-cloudflare-email-routing.sh
```

The script checks:

| Check | What to confirm |
| --- | --- |
| Zone lookup | `harmonia-community.com` resolves to the expected Cloudflare zone id and account id. |
| Email Routing settings | Email Routing is enabled and status is not misconfigured. |
| Email Routing DNS | Cloudflare's required DNS records match the actual DNS records. |
| Routing rules | A rule exists for `info@harmonia-community.com`. |
| Rule action | The action is `forward`, not `drop` or `worker`. |
| Destination | The forward destination includes `ykbballer91@gmail.com`. |
| Destination verification | The destination address has a non-null `verified` timestamp. |
| Catch-all | Catch-all is not unexpectedly dropping or sending mail to a Worker. |
| Duplicate rules | There is not more than one rule matching the same custom address. |

Suggested token permissions should be read-only where possible:

```txt
Zone:Read
Account:Read
Email Routing Rules:Read
Email Routing Addresses:Read
```

## Dashboard Checks If API Is Not Available

Open Cloudflare Dashboard and check:

1. Select the account and zone `harmonia-community.com`.
2. Go to **Email Routing** or **Email Service**.
3. Open **Routing Rules**.
4. Confirm a custom address exists:

| Field | Expected value |
| --- | --- |
| Custom address | `info@harmonia-community.com` |
| Destination | `ykbballer91@gmail.com` |
| Rule status | `Active` |
| Action | `Forward`, not `Drop` or `Worker` |
| Destination address status | `Verified` |

5. Check **Catch-all**:

| Item | What to check |
| --- | --- |
| Enabled/disabled | Confirm expected state. |
| Action | Ensure it is not unexpectedly `Drop` or `Worker`. |
| Destination | If forwarding, confirm the intended destination. |

6. Check **Activity Log** for the exact time of each test message.
7. Check whether DNS records are locked or shown as misconfigured in Email Routing settings.

## Activity Log Decision Table

| Cloudflare Activity Log status | Meaning | Next action |
| --- | --- | --- |
| `Forwarded` | Cloudflare accepted the message and forwarded it to Gmail. | Check Gmail Spam, Promotions, All Mail, filters, blocked senders, and search results. |
| `Rejected` | Cloudflare rejected the message, often due to SPF, DKIM, DMARC, policy, or abuse checks. | Inspect sender authentication details. Cloudflare Email Routing alone may not be able to fix third-party sender authentication failures. |
| `Dropped` | A rule, catch-all, filter, or configuration discarded the message. | Review Routing Rules, Catch-all, Worker routes, and Drop actions. |
| `Processed` | Cloudflare handled the message, often by a configured action such as Worker processing. | Confirm the final action and whether a Worker consumed the message without forwarding. |
| No log | Cloudflare did not receive the message. | Check MX records, SNS notification settings, registered address, bounce status, and whether the sender attempted delivery. |

Given the current DNS result, no Activity Log entry is especially meaningful: mail is probably going to Google MX, not Cloudflare.

## Gmail Search Queries

Run these in Gmail while logged in as `ykbballer91@gmail.com`:

```txt
to:info@harmonia-community.com
"info@harmonia-community.com"
in:anywhere info@harmonia-community.com
in:spam info@harmonia-community.com
from:(instagram OR x OR twitter OR facebook OR meta OR linkedin OR stripe OR cloudflare)
newer_than:7d info@harmonia-community.com
```

Also check:

| Gmail area | What to look for |
| --- | --- |
| Inbox | Direct arrival. |
| Spam | Authentication or reputation filtering. |
| Promotions | SNS and product notifications often land here. |
| All Mail | Archived by a Gmail filter. |
| Filters and blocked addresses | Auto-archive, delete, mark read, category, or forwarding behavior. |

## Test Plan

Send test messages to `info@harmonia-community.com` from each source. Record results immediately after sending.

| Sender | Send time | Cloudflare Activity Log present | Cloudflare status | Gmail arrived | Gmail location | SPF result | DKIM result | DMARC result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gmail personal address |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| iCloud / Outlook / Yahoo |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| Cloudflare notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| Stripe notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| X notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| Instagram notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| Facebook notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |
| LinkedIn notification |  |  | Forwarded / Rejected / Dropped / Processed / none |  | Inbox / Spam / Promotions / All Mail / not found |  |  |  |  |

## Interpreting The Current Situation

Current public DNS points `harmonia-community.com` MX to `smtp.google.com`, not Cloudflare Email Routing. That means inbound mail for `info@harmonia-community.com` should be delivered to Google first. If Cloudflare Email Routing is configured in the dashboard, it is likely not active for public inbound mail until the MX records point to Cloudflare.

The successful loop test from `ykbballer91@gmail.com` to `info@harmonia-community.com` does not prove Cloudflare Email Routing is working. With the current MX, it more likely proves Google-side delivery or alias/routing behavior is working.

## Change Proposal Template

Do not change anything until approved.

If Cloudflare Email Routing should be the authoritative inbound path:

| Proposed change | Impact | Rollback |
| --- | --- | --- |
| Replace apex MX `smtp.google.com` with Cloudflare Email Routing MX records. | All inbound mail for `harmonia-community.com` routes to Cloudflare Email Routing. Existing Google Workspace mailbox behavior may stop unless explicitly accounted for. | Restore the prior MX value `1 smtp.google.com.` |
| Merge SPF to include Cloudflare forwarding, if needed. | Helps authorize Cloudflare forwarding behavior while preserving Google SPF if Google is still used for sending. | Restore previous SPF `v=spf1 include:_spf.google.com ~all`. |

Before changing MX, confirm whether `harmonia-community.com` is supposed to use Google Workspace/Gmail mailboxes, Cloudflare Email Routing, or both in a staged migration.
