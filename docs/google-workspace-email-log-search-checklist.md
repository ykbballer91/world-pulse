# Google Workspace Email Log Search Checklist

## Scope

Use this checklist to diagnose whether messages sent to `info@harmonia-community.com` are reaching Google Workspace and what Google does with them.

Do not change Google Workspace, Gmail, DNS, Cloudflare, SNS, or external service settings while using this checklist. Observe, record, and decide later.

Current premise:

```txt
MX harmonia-community.com -> smtp.google.com
```

Therefore, inbound mail for `info@harmonia-community.com` is expected to reach Google Workspace first.

## Where To Open

Open:

```txt
Google Admin Console > Reporting > Email Log Search
```

If available in your plan, also keep these pages ready for follow-up observation:

```txt
Google Admin Console > Apps > Google Workspace > Gmail > Quarantine
Google Admin Console > Apps > Google Workspace > Gmail > Routing
Google Admin Console > Apps > Google Workspace > Gmail > Default Routing
Google Admin Console > Apps > Google Workspace > Gmail > Compliance
Google Admin Console > Apps > Google Workspace > Gmail > Spam, Phishing and Malware
Gmail as ykbballer91@gmail.com
```

## Search Windows

Run each relevant search twice:

| Window | Use case |
| --- | --- |
| Last 7 days | Fast check for recent SNS or service notifications. |
| Last 30 days | Broader check for intermittent failures or older verification emails. |

If you know the exact SNS test time, search a narrower window around that time first, then expand to 7 days and 30 days.

## Minimum Search Patterns

### Recipient Searches

Start with recipient-only searches.

| Pattern | Search condition |
| --- | --- |
| Original recipient | Recipient: `info@harmonia-community.com` |
| Expected final inbox | Recipient: `ykbballer91@gmail.com` |

Purpose:

| Search | What it tells you |
| --- | --- |
| `recipient: info@harmonia-community.com` | Whether Google saw mail addressed to the domain address. |
| `recipient: ykbballer91@gmail.com` | Whether Google routed, forwarded, or delivered mail to the expected Gmail destination. |

### SNS / External Service Sender Searches

Run these with both recipient filters when possible:

| Sender contains | Recipient |
| --- | --- |
| `instagram` | `info@harmonia-community.com` |
| `instagram` | `ykbballer91@gmail.com` |
| `facebook` | `info@harmonia-community.com` |
| `facebook` | `ykbballer91@gmail.com` |
| `meta` | `info@harmonia-community.com` |
| `meta` | `ykbballer91@gmail.com` |
| `x.com` | `info@harmonia-community.com` |
| `x.com` | `ykbballer91@gmail.com` |
| `twitter` | `info@harmonia-community.com` |
| `twitter` | `ykbballer91@gmail.com` |
| `linkedin` | `info@harmonia-community.com` |
| `linkedin` | `ykbballer91@gmail.com` |
| `stripe` | `info@harmonia-community.com` |
| `stripe` | `ykbballer91@gmail.com` |

If the UI allows free-text sender matching, use **sender contains**. If it requires exact sender addresses, search broad recipient first, open likely entries, then inspect the sender domain.

### Suggested Search Order

1. Last 7 days, recipient `info@harmonia-community.com`.
2. Last 7 days, recipient `ykbballer91@gmail.com`.
3. Last 7 days, recipient `info@harmonia-community.com` plus each sender contains pattern.
4. Last 7 days, recipient `ykbballer91@gmail.com` plus each sender contains pattern.
5. Repeat the same searches for Last 30 days.
6. If a specific test was just sent, search the exact test timestamp plus a small buffer.

## What To Inspect In Each Log Entry

For each matching result, open the message details and record:

| Field | What to capture |
| --- | --- |
| Timestamp | Exact time and timezone. |
| Sender | Full sender address and domain. |
| Recipient | Original recipient shown by Google. |
| Final recipient | Where Google ultimately delivered or attempted delivery. |
| Status | Delivered / Rejected / Quarantined / Spam / Bounced / other. |
| Direction | Inbound / internal / outbound. |
| Message ID | Useful for comparing with sender support or headers. |
| Subject | Only enough to identify the notification. |
| Authentication | SPF, DKIM, DMARC result if shown. |
| Rule / policy | Any routing, compliance, spam, or quarantine rule name shown. |
| Details | Rejection reason, quarantine reason, spam classification, or bounce reason. |

## Result Decision Table

| Log result | Meaning | Next place to check |
| --- | --- | --- |
| Delivered | Google accepted and delivered the message to a mailbox or final recipient. | Check Gmail `All Mail`, `Spam`, `Trash`, categories, and `Filters and Blocked Addresses` for `ykbballer91@gmail.com`. Also inspect headers if the message is found. |
| Rejected | Google refused the message before delivery or due to a policy/routing decision. | Check Gmail `Routing`, `Default Routing`, `Compliance`, sender authentication results, blocked senders, and rejection reason in the log. |
| Quarantined | Google accepted the message but held it in Admin quarantine. | Check `Apps > Google Workspace > Gmail > Quarantine`; search by sender, recipient, and timestamp. Record the quarantine rule and reason. |
| Spam | Google classified the message as spam or routed it according to spam settings. | Check Workspace `Spam, Phishing and Malware`, spam routing settings, Gmail Spam folder, and any allowlist or blocked sender rules. |
| Bounced | Delivery failed after Google accepted or attempted delivery. | Check bounce reason, final recipient, forwarding target, user status, mailbox availability, and external forwarding behavior. |
| No log | Google did not record an inbound message matching the search. | Check SNS/external service notification settings, registered email address, whether a verification email was actually sent, sender bounce/error UI, and spelling of `info@harmonia-community.com`. |

## Detailed Next Steps By Result

### Delivered

If Email Log Search says the message was delivered:

1. In `ykbballer91@gmail.com`, search:

```txt
in:anywhere info@harmonia-community.com
in:spam info@harmonia-community.com
in:trash info@harmonia-community.com
from:(instagram OR facebook OR meta OR x.com OR twitter OR linkedin OR stripe)
```

2. Check:

| Gmail area | Reason |
| --- | --- |
| All Mail | Message may be archived by a filter. |
| Spam | Message may be delivered but hidden from Inbox. |
| Trash | Message may have been deleted by a filter or client. |
| Promotions / Updates | SNS notifications often appear outside Primary. |
| Filters and Blocked Addresses | Filters can archive, delete, mark read, forward, or label messages. |

### Rejected

If Email Log Search says the message was rejected:

1. Record the exact rejection reason.
2. Check whether the log names a routing, compliance, or spam policy.
3. Inspect:

```txt
Apps > Google Workspace > Gmail > Routing
Apps > Google Workspace > Gmail > Default Routing
Apps > Google Workspace > Gmail > Compliance
Apps > Google Workspace > Gmail > Spam, Phishing and Malware
```

4. Record SPF, DKIM, and DMARC results if shown.

Common interpretation:

| Clue | Likely area |
| --- | --- |
| Authentication failure | Sender SPF / DKIM / DMARC, forwarding, or sender reputation. |
| Policy name shown | The named Gmail routing or compliance rule. |
| Recipient not found | User / alias / group / catch-all configuration. |
| Blocked sender | Spam or blocked sender settings. |

### Quarantined

If Email Log Search says the message was quarantined:

1. Open:

```txt
Apps > Google Workspace > Gmail > Quarantine
```

2. Search by:

| Field | Value |
| --- | --- |
| Recipient | `info@harmonia-community.com` |
| Recipient | `ykbballer91@gmail.com` |
| Sender | SNS sender domain |
| Time | Same time as Email Log Search |

3. Record the quarantine name, rule, reason, and available actions.
4. Do not release or delete the message during this checklist unless a separate approval is given.

### Spam

If Email Log Search says the message was spam:

1. Check:

```txt
Apps > Google Workspace > Gmail > Spam, Phishing and Malware
```

2. In Gmail, search:

```txt
in:spam info@harmonia-community.com
in:anywhere from:(instagram OR facebook OR meta OR x.com OR twitter OR linkedin OR stripe)
```

3. Record:

| Item | Value |
| --- | --- |
| Spam classification reason |  |
| Sender authentication | SPF / DKIM / DMARC |
| Was it delivered to Spam? | Yes / no |
| Did a Workspace rule route spam elsewhere? | Yes / no |

### Bounced

If Email Log Search says the message bounced:

1. Record the bounce code and text.
2. Check whether the bounce happened for:

| Target | Interpretation |
| --- | --- |
| `info@harmonia-community.com` | The Workspace address, alias, or group may not exist or may reject mail. |
| `ykbballer91@gmail.com` | Forwarding to the external Gmail account may have failed. |
| Another recipient | Routing or address map may be sending mail somewhere unexpected. |

3. Check user status, group delivery permissions, address maps, and forwarding settings.

### No Log

If no log appears for both 7-day and 30-day searches:

1. Confirm the SNS/external service is configured with exactly:

```txt
info@harmonia-community.com
```

2. Check SNS notification toggles, email verification status, and account security notification settings.
3. Trigger a fresh test email if the service allows it.
4. Check whether the service UI shows a bounce, suppression, or delivery failure.
5. Confirm public DNS still points to Google MX.

No log generally means Google did not receive a matching message.

## Recording Template

Paste or fill this template for each search and result.

```md
## Email Log Search Result

Search time:
Search window: Last 7 days / Last 30 days / custom
Search recipient:
Sender contains:
Service tested:

Found log? Yes / no
Timestamp:
Direction:
Sender:
Original recipient:
Final recipient:
Subject / identifier:
Message ID:
Status: Delivered / Rejected / Quarantined / Spam / Bounced / No log / other

SPF:
DKIM:
DMARC:

Rule or policy shown:
Rejection / quarantine / spam / bounce reason:

Gmail search performed:
Gmail location: Inbox / Spam / Promotions / Updates / All Mail / Trash / not found

Notes:
Next check:
```

## Summary Matrix

Use this table after running all minimum searches.

| Service | 7d log for `info@...` | 7d log for `ykbballer91@...` | 30d log for `info@...` | Status seen | Gmail found? | Suspected layer |
| --- | --- | --- | --- | --- | --- | --- |
| Instagram |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| Facebook |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| Meta |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| X |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| Twitter |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| LinkedIn |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
| Stripe |  |  |  | Delivered / Rejected / Quarantined / Spam / Bounced / No log | Yes / no | Gmail / Workspace / SNS |
