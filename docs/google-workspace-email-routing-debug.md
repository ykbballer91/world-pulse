# Google Workspace / Gmail Email Routing Debug: harmonia-community.com

## Scope

This document is for checking how mail sent to `info@harmonia-community.com` is handled on the Google Workspace / Gmail side.

Do not change settings during this diagnostic pass. Record screenshots or notes first, then prepare a separate change proposal if needed.

Current public DNS indicates that inbound mail for `harmonia-community.com` is routed to Google:

```txt
MX harmonia-community.com 1 smtp.google.com.
```

That means missing SNS notifications are more likely to be handled, filtered, redirected, quarantined, or rejected by Google Workspace / Gmail than by Cloudflare Email Routing.

## Google Workspace Admin Console Checks

Sign in to the Google Admin console with an administrator account for `harmonia-community.com`.

### 1. Confirm The Address Object

Check whether `info@harmonia-community.com` exists as one of these object types:

| Area | Path | What to check |
| --- | --- | --- |
| User | Directory > Users | Is there a user whose primary email is `info@harmonia-community.com`? Is Gmail enabled? Is the user active or suspended? |
| User alias | Directory > Users > target user > User information / Alternate email addresses | Is `info@harmonia-community.com` configured as an alias for another Workspace user? Which user receives it? |
| Group | Directory > Groups | Is `info@harmonia-community.com` a Google Group? If yes, check members, posting permissions, moderation, spam handling, and whether external senders are allowed. |
| Domain alias | Account > Domains > Manage domains | Is `harmonia-community.com` the primary domain, secondary domain, or domain alias? |

Record the result:

| Address | Object type | Owner / members | Status | Notes |
| --- | --- | --- | --- | --- |
| `info@harmonia-community.com` | User / alias / group / unknown |  | Active / suspended / not found |  |

### 2. Confirm The Destination Account

Determine whether `ykbballer91@gmail.com` is inside the same Google Workspace account or is an external consumer Gmail address.

| Check | Expected interpretation |
| --- | --- |
| `ykbballer91@gmail.com` appears under Directory > Users | It is a Workspace-managed user. Admin routing, Vault, quarantine, and Gmail settings may apply. |
| It does not appear under Directory > Users | It is probably an external Gmail account. Workspace routing must be allowed to send externally if forwarding or address maps are used. |

Record:

| Address | Workspace user? | External? | Notes |
| --- | --- | --- | --- |
| `ykbballer91@gmail.com` | Yes / no | Yes / no |  |

### 3. Check Gmail Routing Rules

Go to:

```txt
Apps > Google Workspace > Gmail > Routing
```

Check each organizational unit, especially the root organization and any OU containing the target user or group.

Look for rules that match:

```txt
info@harmonia-community.com
*@harmonia-community.com
all recipients
recognized addresses
non-recognized addresses
external inbound mail
```

Record whether any rule:

| Rule behavior | Risk |
| --- | --- |
| Changes envelope recipient | Mail may be redirected away from the expected inbox. |
| Adds more recipients | Mail may be copied to another user while still delivered normally. |
| Changes route | Mail may be sent to another mail server. |
| Rejects message | Sender may receive bounce, and Gmail inbox will not show the message. |
| Bypasses spam filter | Helpful for selected senders, but should be intentional. |
| Adds spam/phishing headers | Useful for downstream filtering diagnosis. |

Rule inventory:

| Rule name | OU | Match condition | Applies to inbound? | Action | Mentions `info@...`? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

### 4. Check Default Routing

Go to:

```txt
Apps > Google Workspace > Gmail > Default Routing
```

Default routing can affect both recognized and non-recognized addresses. It is commonly used for dual delivery, split delivery, catch-all delivery, or broad forwarding.

Check for:

| Item | What to look for |
| --- | --- |
| Single recipient match | Does a rule explicitly match `info@harmonia-community.com`? |
| Pattern match | Does a regex include `info`, `.*`, or the whole domain? |
| Group membership | Does a group rule include the object that receives `info@...`? |
| All recipients | Does a broad rule apply to every address in the domain? |
| Non-recognized addresses | Is catch-all behavior configured? |
| Reject message | Could unknown or selected recipients be rejected? |
| Modify message | Is the envelope recipient changed, or are extra recipients added? |

Default routing inventory:

| Rule name | Recipient match | Recognized / non-recognized | Action | Adds recipients? | Rejects? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

### 5. Check Recipient Address Map

In Gmail routing, look for address maps used to redirect or forward individual recipients.

Confirm whether there is a map like:

```txt
info@harmonia-community.com -> ykbballer91@gmail.com
```

Important distinction:

| Mode | Meaning |
| --- | --- |
| Redirect / exclude original recipient | Message is sent to the mapped recipient, not the original mailbox. |
| Forward / include original recipient | Message is delivered to the original recipient and copied to the mapped recipient. |

Record:

| Source address | Destination address | Redirect or forward | Active? | Notes |
| --- | --- | --- | --- | --- |
| `info@harmonia-community.com` | `ykbballer91@gmail.com` | Redirect / forward / unknown |  |  |

### 6. Check Catch-all Behavior

Catch-all may be implemented through Default Routing, Routing, or a Google Group.

Check:

| Catch-all condition | What it means |
| --- | --- |
| Non-recognized addresses forwarded to a mailbox | Misspelled or unconfigured addresses may still arrive somewhere. |
| Non-recognized addresses rejected | Messages to addresses not defined as users, aliases, or groups will bounce. |
| Non-recognized addresses routed to a group | Group moderation or external posting rules can block messages. |

If `info@harmonia-community.com` is not found as a user, alias, or group, catch-all behavior becomes a key suspect.

### 7. Check Quarantine, Reject, Compliance, And Spam Rules

Go to the Gmail admin settings and inspect relevant rules:

```txt
Apps > Google Workspace > Gmail > Compliance
Apps > Google Workspace > Gmail > Spam, Phishing and Malware
Apps > Google Workspace > Gmail > Routing
Apps > Google Workspace > Gmail > Default Routing
```

Look for rules involving:

| Rule type | What to check |
| --- | --- |
| Quarantine | Are SNS notifications held in an admin quarantine? Search by sender and recipient. |
| Reject | Are messages from social networks or bulk senders rejected due to content, attachment, sender, or authentication conditions? |
| Content compliance | Are keywords, URLs, or attachment types triggering moderation? |
| Objectionable content | Are social notification templates matching blocked terms? |
| Spam routing | Are spam/phishing-labeled messages routed away from the user? |
| Approved senders / allowlists | Are trusted senders bypassing spam, or are SNS senders missing from the list? |
| Blocked senders | Are domains like `instagram.com`, `facebookmail.com`, `twitter.com`, `x.com`, `linkedin.com`, or `stripe.com` blocked? |

Record:

| Rule area | Rule name | Match | Action | Could affect SNS? | Notes |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### 8. Check External Forwarding Policy

Go to:

```txt
Apps > Google Workspace > Gmail > End User Access
```

Check **Automatic forwarding**.

If users are prevented from automatically forwarding incoming messages, an individual mailbox forwarding rule may not work. Admin-level routing and address maps can still be separate, so record which forwarding mechanism is in use.

| Setting | Value | Impact |
| --- | --- | --- |
| Automatic forwarding | Allowed / disallowed / restricted | If disallowed, user-level Gmail forwarding to external Gmail may fail or be unavailable. |
| External recipients | Allowed / restricted | May affect forwarding to `ykbballer91@gmail.com` if it is external. |

### 9. Search Email Log / Message Investigation

Use Google Admin tools if available:

```txt
Reporting > Email Log Search
Security > Investigation tool
Apps > Google Workspace > Gmail > Quarantine
```

Search around the expected send time:

| Field | Value |
| --- | --- |
| Recipient | `info@harmonia-community.com` |
| Final recipient | `ykbballer91@gmail.com` |
| Sender | SNS sender domain or service |
| Date range | The exact test window plus buffer |

Record:

| Sender | Time | Google accepted? | Final recipient | Status | Spam/quarantine/reject reason | Notes |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | Yes / no |  | Delivered / quarantined / rejected / spam / unknown |  |  |

## Personal Gmail Checks

Perform these checks while signed in to `ykbballer91@gmail.com`.

### 1. Search Everywhere First

Use Gmail search:

```txt
to:info@harmonia-community.com
"info@harmonia-community.com"
in:anywhere info@harmonia-community.com
in:spam info@harmonia-community.com
in:trash info@harmonia-community.com
newer_than:7d info@harmonia-community.com
from:(instagram OR x OR twitter OR facebook OR meta OR linkedin OR stripe OR cloudflare)
```

Check:

| Location | Meaning |
| --- | --- |
| Inbox | Message arrived normally. |
| Spam | Gmail classified it as spam/phishing. |
| Promotions | SNS/product mail may be categorized here. |
| All Mail | Message may have been archived by a filter. |
| Trash | Message may have been deleted by a filter or manually. |
| Not found | Check Workspace logs and sender-side delivery. |

### 2. Accounts And Import

Go to:

```txt
Gmail > Settings > See all settings > Accounts and Import
```

Check:

| Section | What to verify |
| --- | --- |
| Send mail as | Is `info@harmonia-community.com` added only as a sending identity? This does not prove receiving is configured. |
| Check mail from other accounts | Is Gmail fetching mail from a Google Workspace mailbox or another account using POP? If yes, check errors and last fetch time. |
| Grant access to your account | Is another user/delegate modifying or archiving messages? |

### 3. Forwarding And POP/IMAP

Go to:

```txt
Gmail > Settings > See all settings > Forwarding and POP/IMAP
```

Check:

| Section | What to verify |
| --- | --- |
| Forwarding | Is forwarding enabled? If yes, where does it forward, and what happens to the Gmail copy? |
| POP download | Is POP enabled, and could another client be downloading/deleting messages? |
| IMAP access | Is an external mail client connected and applying rules? |

For Gmail automatic forwarding, spam is not forwarded by default. If SNS messages are classified as spam before forwarding, they may remain in Spam and never reach the forward destination.

### 4. Filters And Blocked Addresses

Go to:

```txt
Gmail > Settings > See all settings > Filters and Blocked Addresses
```

Look for filters matching:

```txt
info@harmonia-community.com
instagram
facebook
meta
twitter
x.com
linkedin
stripe
notification
no-reply
noreply
```

Risky filter actions:

| Action | Impact |
| --- | --- |
| Skip the Inbox / Archive | Message appears only in All Mail or label. |
| Delete it | Message may be in Trash or gone after retention. |
| Mark as read | User may miss it. |
| Forward it | Message may go elsewhere. |
| Never send it to Spam | Helpful if intentionally used for trusted senders. |
| Blocked sender | Message may be routed to Spam. |

### 5. Spam, All Mail, Trash, Categories

Check these Gmail areas manually:

| Area | Query or action |
| --- | --- |
| Spam | `in:spam info@harmonia-community.com` |
| All Mail | `in:anywhere info@harmonia-community.com` |
| Trash | `in:trash info@harmonia-community.com` |
| Promotions | Search within category if available. |
| Updates | SNS and service notices often land here. |

Open any found message and inspect **Show original** for:

| Header result | What to record |
| --- | --- |
| SPF | pass / fail / softfail / neutral |
| DKIM | pass / fail / none |
| DMARC | pass / fail / none |
| Delivered-To | Which mailbox received it. |
| X-Gm-Original-To | Original envelope recipient if Google routing changed it. |
| Authentication-Results | Sender authentication and forwarding clues. |

## Google Workspace Vs Cloudflare Email Routing Decision Table

| Requirement | Prefer Google Workspace / Gmail | Prefer Cloudflare Email Routing |
| --- | --- | --- |
| Need real mailboxes for domain users | Yes. Google Workspace provides mailbox storage, Gmail UI, search, admin logs, Vault options, and user management. | No. Cloudflare Email Routing is forwarding-only. |
| Need to send as `info@harmonia-community.com` through authenticated SMTP/Gmail | Yes. Use Google Workspace sending, aliases, DKIM, SPF, and DMARC alignment. | No. Cloudflare Email Routing is not an SMTP sending service. |
| Need simple forwarding aliases to external inboxes | Possible, but requires Workspace routing, aliases, groups, or forwarding policies. | Yes, if inbound MX points to Cloudflare and destination is verified. |
| Need Google Groups, moderation, collaborative inbox, or internal permissions | Yes. | No. |
| Need admin email logs and quarantine controls | Yes. | Limited to Cloudflare Email Routing activity. |
| Want to avoid paying for a mailbox just to forward one address | Maybe not ideal. | Often a good fit. |
| Current MX already points to `smtp.google.com` | Keep Google unless there is a deliberate migration plan. | Requires MX change and impact review. |
| Existing Google Workspace users depend on domain mail | Usually keep Google as primary MX. | Changing MX to Cloudflare could disrupt mailbox delivery unless carefully designed. |
| Main issue is SNS messages missing from Gmail | Investigate Google logs, spam, quarantine, groups, and filters first. | Only investigate Cloudflare if MX is changed to Cloudflare or logs prove Cloudflare received messages. |

## Current Working Hypothesis

Because public MX points to `smtp.google.com`, the next best diagnostic step is Google Admin Console message tracing for `info@harmonia-community.com`, followed by checking whether `info@harmonia-community.com` is a user, alias, group, address map, or catch-all target.

If Google Email Log Search shows messages are accepted and delivered to `ykbballer91@gmail.com`, the issue is likely in personal Gmail categories, Spam, filters, All Mail, Trash, or client-side handling.

If Google Email Log Search shows rejected, quarantined, or spam-routed messages from SNS senders, focus on Workspace Gmail compliance, spam, quarantine, and sender authentication results.

If Google Email Log Search has no record, confirm the SNS service is sending to the exact address and check whether the sender received a bounce.

## References

- Google Workspace Gmail admin settings: https://support.google.com/a/answer/2786758
- Google Workspace Default routing: https://support.google.com/a/answer/2368153
- Google Workspace Gmail routing settings: https://support.google.com/a/answer/6297084
- Google Workspace address maps / forwarding: https://support.google.com/a/answer/4524505
- Gmail automatic forwarding: https://support.google.com/mail/answer/10957
- Gmail filters and blocked addresses: https://support.google.com/mail/answer/6579
- Gmail Accounts and Import troubleshooting: https://support.google.com/mail/answer/7239777
