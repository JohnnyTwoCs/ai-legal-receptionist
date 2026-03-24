# AI Legal Receptionist

A smart voicemail replacement for family law firms. Built by [Ledger.AI](https://getledger.net).

When everyone's with clients, the AI handles intake, scheduling, and follow-up so no caller falls through the cracks.

## What It Does

- **Voice agent** (via Retell AI) answers calls, collects intake info, books consultations on Google Calendar, and sends confirmation emails
- **Chat agent** (via Claude API + Pinecone RAG) handles text-based intake with real-time field extraction and NJ family law knowledge
- **Smart routing**: new clients get intake flow, existing clients get parsed callbacks, general questions answered from knowledge base
- **Never guesses**: if the AI doesn't know something, it says so and takes a callback

## Live Demo

- **Phone**: +1 (877) 735-5707
- **Web**: [Chat Demo](https://legal-receptionist.onrender.com/chat-demo) | [Voice Demo](https://legal-receptionist.onrender.com/voice-demo)

## Stack

| Component | Tech |
|-----------|------|
| Voice AI | Retell AI (Claude 4.5 Haiku) |
| Chat AI | Claude Sonnet (Anthropic API) |
| RAG | Pinecone + OpenAI Embeddings |
| Scheduling | Google Calendar API |
| Intake Logging | Google Sheets API |
| Email | Google Workspace (Gmail) |
| Backend | Flask + Gunicorn |
| Frontend | Vanilla HTML/JS + WebGL (OGL) |

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env  # Fill in your API keys
python -m tools.legal_receptionist.ingest  # Index knowledge base into Pinecone
python server.py  # http://localhost:5001
```

## Deploy to Render

Build command: `pip install -r requirements.txt`
Start command: `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

Set environment variables from `.env.example` in the Render dashboard.

---

Built by [Jon Roth](https://linkedin.com/in/jon-s-roth) at [Ledger.AI](https://getledger.net)
