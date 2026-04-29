# BLS Smart Customer Service Agent

A 100-minute MVP web-based customer service chatbot for AllCPR / BLS training built with **Python + Streamlit**.

## Features

- Chat UI titled "BLS Smart Customer Service Agent"
- Answers **only** from the embedded FAQ knowledge base (21 topics)
- Refuses emergency/medical procedure questions and escalates via email
- Escalates unknown questions via SMTP email with timestamp + AI summary
- Optional OpenAI integration to polish answers (never invents new information)
- Keyword/similarity matching — no hallucinations

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your SMTP credentials and optional OpenAI key
```

### 3. Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | No | If set, uses GPT-3.5 to polish answers |
| `SMTP_HOST` | Yes (for email) | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | Yes (for email) | Usually `587` |
| `SMTP_USER` | Yes (for email) | Your email login |
| `SMTP_PASSWORD` | Yes (for email) | App password (Gmail) |
| `ALERT_EMAIL_TO` | Yes (for email) | Support inbox |
| `ALERT_EMAIL_FROM` | Yes (for email) | Sender address |

> **Gmail users:** Generate an [App Password](https://support.google.com/accounts/answer/185833) — do not use your main Gmail password.

## FAQ Topics Covered

1. Online course access
2. Login issues
3. Browser troubleshooting
4. CPR vs BLS
5. ARC vs AHA
6. Same-day enrollment
7. What to bring to class
8. Email requirement
9. Rescheduling
10. Cancellations / refunds
11. Certification timing
12. Certificate retrieval
13. Expedited certification
14. CEUs
15. Group / on-site training
16. Locations
17. Hands-on experience
18. Accreditation
19. First-time students / renewals
20. Receipts
21. Feedback
22. Contact information

## How It Works

1. User types a question in the browser.
2. The agent checks for emergency/medical keywords — if matched, it refuses and sends an email alert.
3. Otherwise, FAQ keyword matching scores each FAQ entry.
4. If a match is found (score ≥ 1), the answer is returned (optionally polished by OpenAI).
5. If no match, the agent replies that it cannot help and sends an email escalation with the question, an AI-generated summary, and a timestamp.

## Files

```
app.py            — Main Streamlit application + FAQ data
requirements.txt  — Python dependencies
.env.example      — Environment variable template
README.md         — This file
```
