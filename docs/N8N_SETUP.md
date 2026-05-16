# n8n Setup Guide

## Prerequisites

- Docker + Docker Compose
- Google account (for Sheet)
- Slack workspace (for approvals)
- Gmail account (for Drafts)

## Initial Setup

1. `docker compose up -d`
2. Open http://localhost:5678 and complete the n8n onboarding (set a local password)
3. Settings → Credentials → add:
   - **Google Sheets OAuth2** (n8n provides the OAuth flow)
   - **Gmail OAuth2** (same)
   - **Slack Bot** (paste your bot user OAuth token)
   - **GitHub** (personal access token with `repo` scope)

## Workflow Import

For each file in `workflows/n8n/*.json`:
1. Workflows → Import → upload the JSON
2. Open the workflow and verify all credentials are reattached
3. Activate

## Demo Google Sheet

- Sheet name: `Boldr Demo Tickets`
- Tab `tickets_input`: import `eval/data/tickets_input.csv`
- Tab `eval_labels`: import `eval/data/eval_labels.csv` (held-out, agent never sees)
- Share with the email of the Google credential used by n8n

## FastAPI Service

n8n containers reach the host's FastAPI service at `http://host.docker.internal:8000`. Always start it via:

```bash
uv run uvicorn intel_engine.api:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

- If Google Sheets trigger fails: re-auth the credential
- If HTTP node returns 500: check FastAPI logs
- If n8n container can't reach host: ensure `extra_hosts` is set in docker-compose.yml
