# 📸 Transparent Classroom Photo Grabber

> Automated photo downloader with cron scheduling, Telegram notifications, and Docker support

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

## 🚀 Features

- 🔐 Secure authentication to Transparent Classroom
- 📥 Automatic photo downloads with smart caching
- � EXIF/IPTC metadata embedding (GPS, timestamps, descriptions)
- ⏰ **Cron scheduling** - hourly, daily, or custom cron expressions
- 📱 **Telegram bot** - instant notifications + remote control
  - Get notified when photos are downloaded
  - Switch between compressed/original quality via bot commands
  - Telegram is **completely optional**
- 🐳 Docker & Kubernetes ready
- 🔄 Incremental downloads (skip existing photos)

## 📋 Requirements

### System Dependencies
- Python 3.14 or higher
- `exiftool` for IPTC metadata (optional but recommended)

## 🔧 Installation

### Local Installation

```bash
# Clone the repository
cd tc-photo-grabber

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install exiftool (optional but recommended)
# macOS:
brew install exiftool
# Ubuntu/Debian:
sudo apt-get install libimage-exiftool-perl
```

### Docker Installation

```bash
# Build the Docker image
docker build -t tc-photo-grabber:latest .
```

## ⚙️ Configuration

### Option 1: Environment Variables

Create a `.env` file (see `.env.example`):

```bash
TC_EMAIL=your.email@example.com
TC_PASSWORD=your_password
SCHOOL=12345
CHILD=67890
SCHOOL_LAT=41.9032
SCHOOL_LNG=-87.6663
SCHOOL_KEYWORDS=school, montessori, chicago
OUTPUT_DIR=./photos
CACHE_DIR=./cache

# Optional: Cron expression for scheduling (takes precedence over SCHEDULE)
# CRON_EXPRESSION=0 2 * * *

# Optional: Timezone for cron scheduling (default: UTC)
# TZ=America/Chicago

# Optional: Telegram notifications
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
# TELEGRAM_CHAT_ID=@yourchannel or -1001234567890
```

### Option 2: YAML Config File

Create `~/.config/transparent-classroom-photos-grabber/config.yaml`:

```yaml
email: your.email@example.com
password: your_password
school_id: 12345
child_id: 67890
school_lat: 41.9032
school_lng: -87.6663
school_keywords: school, montessori, chicago
output_dir: ./photos
cache_dir: ./cache
cache_timeout: 14400
# Optional: Cron expression for scheduling
# cron_expression: "0 2 * * *"
# Optional: Timezone for cron scheduling (default: UTC)
# timezone: "America/Chicago"
# Optional: Telegram notifications
# telegram_bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
# telegram_chat_id: "@yourchannel"
```

## 🎯 Quick Start

### Run Once
```bash
python -m src
```

### Run on Schedule
```bash
# Daily at 2 AM
python -m src --cron --schedule daily

# Every 30 min, Mon-Fri, 8am-6pm
python -m src --cron --cron-expression "*/30 8-17 * * 1-5"

# With timezone
export TZ="America/Chicago"
python -m src --cron --cron-expression "0 2 * * *"
```

### Other Options
```bash
python -m src --show-config  # View config
python -m src --dry-run      # Test without downloading
python -m src --verbose      # Debug mode
python -m src --cron --schedule "every day at 10:30"

# Run hourly
python -m src --cron --schedule hourly
```

#### Using Cron Expressions

## 📱 Telegram Bot (Optional)

The Telegram bot runs in a background thread and responds instantly to commands. **Telegram is completely optional** - the app works fine without it.

### Setup
1. Create bot with [@BotFather](https://t.me/botfather) - send `/newbot` and follow instructions
2. Get chat ID:
   - For personal chat: send a message to your bot, then visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - For channel: add bot as admin, use `@channelname` or numeric ID
3. Set env vars:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=@yourchannel  # or numeric ID
```

### Commands
- `/sendfile` - Send photos as files (original quality)
- `/sendphoto` - Send photos compressed
- `/status` - Check current mode

Settings persist in `cache/telegram_settings.json`.

### Register Commands
Open [@BotFather](https://t.me/botfather), send `/setcommands`, select your bot, then paste:
```
sendfile - Send photos as files (original quality)
sendphoto - Send photos compressed
status - Check current photo sending mode
```

## 🐳 Docker

```bash
# Run once
docker run --rm -v $(pwd)/photos:/photos -e MODE=cli tc-photo-grabber

# Run with cron
docker run -d \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/cache:/cache \
  -e MODE=cron \
  -e CRON_EXPRESSION="*/30 8-17 * * 1-5" \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -e TELEGRAM_CHAT_ID="your_chat_id" \
  tc-photo-grabber
```

## ☸️ Kubernetes

```bash
# Create secret
kubectl create secret generic tc-photo-grabber-secret \
  --from-literal=TC_EMAIL='your@email.com' \
  --from-literal=TC_PASSWORD='password' \
  --from-literal=SCHOOL='12345' \
  --from-literal=CHILD='67890'

# Deploy
kubectl apply -f k8s-deployment.yaml
kubectl logs -f deployment/tc-photo-grabber
```

Edit `k8s-deployment.yaml` to customize schedule (default: daily at 2 AM).

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format & lint
black src/ && pylint src/
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Credits

Based on [Harper Reed's](https://github.com/harperreed) Rust implementation, preserving original auth logic from `get_photos.py`.
