# Family Law – Email Keyword Alert Workflow

An **n8n** automation that monitors your Gmail inbox every hour, detects emails related to active family law matters, looks up the case in **myCase**, identifies the lead attorney or paralegal, and sends a notification via **Slack** and/or **Telegram**.

---

## Architecture & Privacy Model

```
Gmail (last 1h)
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Privacy Filter & Keyword Extractor  (n8n Code node) │
│                                                       │
│  • Runs 100% LOCALLY inside n8n                      │
│  • Strips PII: names, email addresses, phone, SSN    │
│  • Matches keywords from config/keywords.json        │
│  • Extracts case reference number (regex)            │
│  • Outputs: matched categories + safe metadata ONLY  │
│                                                       │
│  ✗ Raw email body is NEVER forwarded anywhere        │
│  ✗ No LLM is called — pure local string matching     │
└─────────────────────────────────────────────────────┘
     │
     ▼  (only if keywords matched)
myCase API  →  Get case team  →  Build notification
     │
     ▼
Slack DM / Channel  +  Telegram message
```

### What leaves n8n (and what does NOT)

| Data | Stays local | Sent externally |
|---|---|---|
| Full email body | ✅ Never leaves n8n | — |
| Sender full name/address | ✅ Stripped to domain only | — |
| Email subject | ✅ PII-stripped before use | — |
| Matched keyword categories | — | ✅ myCase API query |
| Case reference number | — | ✅ myCase API query |
| Case number + staff names | — | ✅ Slack / Telegram |

---

## Workflow Steps

1. **Schedule Trigger** – fires every 60 minutes
2. **Gmail** – fetches up to 50 emails received in the last hour from INBOX
3. **Privacy Filter & Keyword Extractor** – local Code node; strips PII, matches keywords
4. **Keyword gate** – skips emails with no relevant keywords
5. **myCase – Search Cases** – searches by case reference or keyword category
6. **Case gate** – if no case found, sends a fallback alert to the default Slack channel
7. **myCase – Get Case Staff** – retrieves lead attorney and paralegal
8. **Build Notification Payload** – formats a safe, PII-free message
9. **Slack** – sends a DM to the matched staff member (or fallback channel)
10. **Telegram** – sends a message if the staff member has a Telegram chat ID configured

---

## Prerequisites

| Service | What you need |
|---|---|
| n8n | Self-hosted or n8n Cloud (v1.30+) |
| Gmail | Google OAuth2 credential in n8n |
| myCase | API token (Settings → Integrations → API in myCase) |
| Slack | Bot token with `chat:write`, `im:write` scopes |
| Telegram | Bot token from [@BotFather](https://t.me/BotFather) |

---

## Setup

### 1. Install / open n8n

```bash
# Docker (quickest)
docker run -it --rm \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

Then open `http://localhost:5678`.

### 2. Add Credentials in n8n

Go to **Settings → Credentials → Add Credential** for each:

- **Gmail OAuth2** – follow the Google Cloud Console OAuth2 setup
- **Slack API** – paste your bot token
- **HTTP Request (myCase)** – use Header Auth: `Authorization: Token token=<YOUR_TOKEN>`
- **HTTP Request (Telegram)** – no credential needed; token is in the URL via env var

### 3. Set environment variables

In n8n (**Settings → Environment Variables** or your `.env`):

```
MYCASE_BASE_URL=https://app.mycase.com/api/v1
MYCASE_API_TOKEN=your_token_here
SLACK_BOT_TOKEN=xoxb-...
SLACK_FALLBACK_CHANNEL=C0000000000   # channel ID for unmatched-case alerts
TELEGRAM_BOT_TOKEN=your_bot_token
```

See `config/.env.example` for reference.

### 4. Import the workflow

1. In n8n, go to **Workflows → Import from file**
2. Select `workflow/email-notification-workflow.json`
3. Open the imported workflow and update credential IDs:
   - `Gmail – Fetch Last Hour` node → select your Gmail OAuth2 credential
   - `Slack – Send DM / Channel` node → select your Slack credential
4. Save

### 5. Configure keywords

Edit `config/keywords.json` to add or remove keywords per category. The same list is pasted into the **Privacy Filter & Keyword Extractor** Code node in the workflow — keep them in sync.

### 6. Configure staff routing

Edit `config/notification-routing.json`:
- Add real Slack user IDs (e.g. `U0ABC1234`) for each staff member
- Add Telegram chat IDs where applicable (staff must send `/start` to your bot first)
- Update the `slack_user_id` / `telegram_chat_id` fields in myCase's user records or hardcode them in the **Build Notification Payload** Code node

### 7. Activate

Toggle the workflow to **Active**. It will run automatically every hour.

---

## Customising keywords

Open `config/keywords.json`. Each category has a label and a list of keywords:

```json
"urgent": {
  "label": "URGENT",
  "keywords": ["urgent", "emergency", "hearing tomorrow", ...]
}
```

The **URGENT** category triggers an additional ping to `#urgent-alerts` (configure `urgency_overrides` in `notification-routing.json`).

---

## Adding a new notification channel

The workflow is modular. To add email (SendGrid, etc.) or Teams:
1. Add a new **IF** node branching off **Build Notification Payload**
2. Check `$json.notify_via.includes('teams')` (or your channel name)
3. Add the corresponding send node

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No emails fetched | Check Gmail credential, confirm `newer_than:1h` filter works in Gmail search |
| Keywords not matching | Run the Code node manually with a test email payload; check casing |
| myCase returns 401 | Re-generate the API token in myCase Settings |
| Slack message says "channel not found" | Use channel/user **ID** (starts with C or U), not the name |
| Telegram 400 error | Make sure the user has sent `/start` to the bot to open a chat |

---

## Security notes

- Never commit real API tokens. Use n8n's built-in credential store or environment variables.
- The Gmail OAuth2 scope needed is `https://www.googleapis.com/auth/gmail.readonly` — read-only, the workflow never sends emails.
- myCase API calls use HTTPS only.
- Consider restricting your n8n instance behind a VPN or password if self-hosted.
