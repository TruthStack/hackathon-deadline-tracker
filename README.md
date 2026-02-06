# HLUEAS - Hackathon Lifecycle Urgency & Execution Automation System

> **A Continuous Deadline Survival Engine** that auto-detects Devpost hackathon participation, computes urgency scores, and escalates Telegram alerts until submission.

## 🎯 What This Solves

If you participate in multiple Devpost hackathons, you face:
- **Missed deadlines** - Single email reminders get ignored
- **Cognitive overload** - Too many hackathons to track manually
- **Poor prioritization** - No urgency ranking across events
- **Last-minute panic** - No escalating alerts as deadlines approach

**HLUEAS** solves this by:
1. ✅ Auto-detecting your registered hackathons from Devpost
2. ✅ Computing urgency scores based on time remaining
3. ✅ Escalating Telegram notifications (CRITICAL → HIGH → MEDIUM → LOW)
4. ✅ Running 24/7 via GitHub Actions (100% free, no hosting)

---

## 🚀 Quick Start

### 1. Prerequisites

- **Devpost account** with registered hackathons
- **Telegram account** and bot token ([Get from @BotFather](https://t.me/BotFather))
- **GitHub account** (for Actions automation)

### 2. Setup

1. **Clone this repository**
   ```bash
   git clone <your-repo-url>
   cd hackathon-tracking-automation
   ```

2. **Create Telegram Bot**
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow instructions
   - Copy the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
   - Get your Chat ID:
     - Message your bot
     - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
     - Find your `chat.id` in the response

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   DEVPOST_USERNAME=your_devpost_username
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=123456789
   TOP_N_HACKATHONS=3
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Test Locally

Run in dry-run mode (no notifications sent):
```bash
cd src
python main.py --dry-run
```

Run live test:
```bash
cd src
python main.py
```

### 4. Deploy to GitHub Actions

1. **Add GitHub Secrets**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `DEVPOST_USERNAME`
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_CHAT_ID`
     - `TOP_N_HACKATHONS` (optional, defaults to 3)

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial HLUEAS setup"
   git push origin main
   ```

3. **Enable GitHub Actions**
   - Go to Actions tab
   - Enable workflows if prompted
   - The workflow will run every 3 hours automatically

4. **Manual Trigger** (optional)
   - Go to Actions → Hackathon Deadline Watch
   - Click "Run workflow"

---

## 📊 How It Works

```
GitHub Actions (every 3h)
    ↓
Scrape Devpost Profile
    ↓
Extract Active Hackathons
    ↓
Compute Urgency Scores
    ↓
Filter by Notification Interval
    ↓
Send Telegram Alerts
    ↓
Update State File
```

### Escalation Logic

| Hours Left | Alert Level | Notification Interval | Emoji |
|------------|-------------|----------------------|-------|
| ≤ 3 | 🔴 CRITICAL | Every 1 hour | 🔴 |
| ≤ 12 | 🟠 HIGH | Every 3 hours | 🟠 |
| ≤ 48 | 🟡 MEDIUM | Every 12 hours | 🟡 |
| ≤ 168 (7d) | 🟢 LOW | Every 24 hours | 🟢 |
| > 168 | ⚪ IGNORE | Weekly summary | ⚪ |

### Priority Ranking

Hackathons are ranked by:
- **50%** - Time urgency (1 / hours_remaining)
- **20%** - Prize amount (normalized)
- **30%** - Tag match score (future feature)

Only the **top N** hackathons are tracked to prevent cognitive overload.

---

## 🛠️ Project Structure

```
hackathon-tracking-automation/
├── .github/
│   └── workflows/
│       └── deadline-watch.yml    # GitHub Actions automation
├── src/
│   ├── __init__.py
│   ├── scraper.py                # Devpost profile scraper
│   ├── urgency.py                # Urgency calculation engine
│   ├── notifier.py               # Telegram notification sender
│   ├── state.py                  # State persistence manager
│   └── main.py                   # Main orchestrator
├── data/
│   └── state.json                # Notification history (auto-generated)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEVPOST_USERNAME` | ✅ | Your Devpost username |
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | Your Telegram chat ID |
| `TOP_N_HACKATHONS` | ❌ | Max hackathons to track (default: 3) |
| `DRY_RUN` | ❌ | Set to `true` for testing (default: false) |

---

## 🧪 Testing

### Unit Tests (Future)
```bash
pytest tests/ -v
```

### Dry Run Mode
```bash
cd src
python main.py --dry-run
```

### Connection Test
```python
from notifier import TelegramNotifier

notifier = TelegramNotifier(bot_token="YOUR_TOKEN", chat_id="YOUR_CHAT_ID")
notifier.test_connection()
```

---

## 📝 Example Output

```
============================================================
HLUEAS - Hackathon Deadline Watch
============================================================

📋 Configuration:
  Devpost User: johndoe
  Top N Hackathons: 3
  Dry Run: False

🔍 Scraping Devpost profile...
✅ Found 5 active hackathons

⚡ Computing urgency scores...
✅ 3 hackathons require attention

📊 Urgency Summary:
  1. 🔴 AI Safety Hackathon
     Level: CRITICAL | Hours Left: 2.5h
  2. 🟠 Climate Tech Challenge
     Level: HIGH | Hours Left: 8.3h
  3. 🟡 Web3 Builder Fest
     Level: MEDIUM | Hours Left: 36.2h

🔔 Checking notification state...
✅ 2 hackathons need notification

📤 Sending notifications...
✅ Sent 2 notifications

💾 Updating state...
✅ State updated

============================================================
✨ HLUEAS run complete!
============================================================
```

---

## 🚨 Troubleshooting

### Scraper Not Finding Hackathons
- Verify your Devpost username is correct
- Check if you have active hackathon registrations
- Devpost HTML structure may have changed (open an issue)

### Telegram Notifications Not Received
- Verify bot token and chat ID are correct
- Test connection: `notifier.test_connection()`
- Check if bot is blocked or chat is archived

### GitHub Actions Failing
- Check Actions logs for error messages
- Verify all secrets are set correctly
- Ensure repository has write permissions for Actions

---

## 🔒 Security

- **Never commit `.env` file** - It contains secrets
- **Use GitHub Secrets** for Actions deployment
- **Rotate tokens** if accidentally exposed
- **State file** is safe to commit (contains no secrets)

---

## 📈 Future Enhancements

- [ ] Tag-based interest matching
- [ ] Submission confirmation detection
- [ ] Multi-platform support (MLH, Devfolio)
- [ ] Custom urgency thresholds
- [ ] Discord/Slack integration
- [ ] Web dashboard

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built to solve the **Persistent Deadline Escalation Gap** for multi-hackathon participants.

**Execution > Registration**

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/hackathon-tracking-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/hackathon-tracking-automation/discussions)

---

**Made with ⚡ by hackathon enthusiasts, for hackathon enthusiasts**
