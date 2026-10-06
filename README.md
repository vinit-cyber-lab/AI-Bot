# AI-Bot

AI-Bot is a lightweight automation bot built for a first production-ready version of a full automation suite.

It is designed to:
- monitor GitHub repositories
- check system health
- backup local data
- send notifications to Discord and Telegram
- run scheduled tasks automatically
- support manual execution from the terminal or future dashboard

## Included in v1

- GitHub repository health monitoring
- System health checks (CPU, memory, disk)
- Local backup generation
- Daily summary reporting
- Discord webhook notifications
- Telegram bot notifications
- Scheduler-based automation loop

## Project layout

```text
AI-Bot/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config.py
├── bot.py
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── services/
│   ├── __init__.py
│   ├── github_service.py
│   ├── notifications.py
│   └── system_service.py
└── backups/
    └── .gitkeep
```

## Quick start

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Update `.env` with your own values.

5. Run the bot:

```bash
python bot.py
```

## Environment variables

At minimum, configure:

```env
BOT_NAME=AI-Bot
BOT_VERSION=1.0.0
GITHUB_REPO=vinit-cyber-lab/AI-Bot
GITHUB_TOKEN=your_github_token
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

You can leave Discord or Telegram blank if you do not want notifications there.

## What the bot does

### 1. GitHub monitor
Checks the configured GitHub repository and reports:
- repo name
- default branch
- visibility
- stars
- watchers
- forks
- open issues
- last push time

### 2. System health
Collects system metrics:
- CPU percent
- memory usage
- disk usage
- platform info

### 3. Backup task
Creates a JSON backup in the `backups/` folder.

### 4. Daily summary
Generates a summary and sends it to channels configured in `.env`.

## Scheduling

The first version uses a simple scheduler:

- GitHub monitor: every 5 minutes
- Health check: every 10 minutes
- Backup: every hour
- Daily summary: daily at 09:00

## Run modes

- Local terminal: `python bot.py`
- Background in Linux/macOS: `nohup python bot.py > logs/bot.log 2>&1 &`
- Optional future deployment: Docker, VPS, or GitHub Actions

## Notes

This is the first version of the full automation suite. It is intentionally simple and production-friendly, but you can extend it later with:
- WhatsApp via Twilio
- Slack
- Email alerts
- SQLite database
- Flask/FastAPI dashboard
- GitHub Actions deployment
- Docker runtime

## License

MIT
