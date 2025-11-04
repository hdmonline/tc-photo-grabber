# 📸 Transparent Classroom Photos Grabber (Python)

> Python implementation with cron scheduling and Docker/Kubernetes support

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

## 🌟 Overview

This is a Python rewrite of the Transparent Classroom Photos Grabber with added cron scheduling capabilities for automated, periodic photo downloads. The application can run as:

1. **CLI tool** - Run once to download photos
2. **Cron scheduler** - Run continuously with scheduled downloads
3. **Docker container** - Deploy to Kubernetes or any container platform

The authentication and configuration logic is preserved from the original Python implementation, ensuring compatibility and reliability.

## 🚀 Features

- ✅ Secure authentication to Transparent Classroom (original implementation)
- ✅ Automatic crawling of all posts with photos
- ✅ Smart caching to avoid unnecessary downloads
- ✅ Embedded EXIF metadata including GPS coordinates and timestamps
- ✅ **NEW: Cron scheduling** for automated downloads
  - Simple schedules: hourly, daily, weekly, custom intervals
  - **Unix cron expressions** for precise scheduling
- ✅ **NEW: Telegram notifications** 📱
  - Get notified when new photos are downloaded
  - Receive the photos directly in your Telegram chat/channel
- ✅ **NEW: Docker support** for containerized deployment
- ✅ **NEW: Kubernetes ready** with example manifests
- ✅ Skip already downloaded photos for incremental updates
- ✅ Configurable via environment variables or YAML config file

## 📋 Requirements

### System Dependencies
- Python 3.11 or higher
- `exiftool` for IPTC metadata (optional but recommended)

### Python Dependencies
- requests
- beautifulsoup4
- python-dotenv
- PyYAML
- piexif
- schedule
- croniter (for cron expression support)
- colorama (optional)

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

## 🎯 Usage

### CLI Mode (Run Once)

```bash
# Basic usage - downloads to ./photos
python -m src

# Custom output directory
python -m src --output /path/to/photos

# Show current configuration
python -m src --show-config

# Dry run (see what would be downloaded)
python -m src --dry-run

# Verbose output for debugging
python -m src --verbose
```

### Cron Mode (Scheduled Downloads)

#### Using Simple Schedules

```bash
# Run with daily schedule (default runs at 2:00 AM)
python -m src --cron --schedule daily

# Run every 6 hours
python -m src --cron --schedule "every 6 hours"

# Run every day at 10:30
python -m src --cron --schedule "every day at 10:30"

# Run hourly
python -m src --cron --schedule hourly
```

#### Using Cron Expressions

For more precise scheduling, you can use standard Unix cron expressions:

```bash
# Run daily at 2:00 AM
python -m src --cron --cron-expression "0 2 * * *"

# Run every 30 minutes
python -m src --cron --cron-expression "*/30 * * * *"

# Run every 6 hours
python -m src --cron --cron-expression "0 */6 * * *"

# Run Monday to Friday at 9:00 AM
python -m src --cron --cron-expression "0 9 * * 1-5"

# Or set via environment variable
export CRON_EXPRESSION="0 2 * * *"
python -m src --cron

# With timezone (default is UTC)
export TZ="America/Chicago"
export CRON_EXPRESSION="0 2 * * *"  # 2 AM Central Time
python -m src --cron
```

**Cron Expression Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, both 0 and 7 are Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

**Notes:** 
- Cron expressions take precedence over `--schedule` when both are provided.
- Cron times are interpreted in the timezone specified by the `TZ` environment variable (default: UTC).
- Common timezones: `America/New_York`, `America/Chicago`, `America/Los_Angeles`, `Europe/London`, `Asia/Tokyo`

### Docker Usage

#### Run Once (CLI Mode)

```bash
docker run --rm \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/.env:/app/.env \
  -e MODE=cli \
  tc-photo-grabber:latest
```

#### Run in Cron Mode

```bash
# Using simple schedule
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/.env:/app/.env \
  -e MODE=cron \
  -e SCHEDULE=daily \
  tc-photo-grabber:latest

# Using cron expression (takes precedence over SCHEDULE)
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/.env:/app/.env \
  -e MODE=cron \
  -e CRON_EXPRESSION="0 2 * * *" \
  tc-photo-grabber:latest

# Using cron expression with immediate run on startup
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/.env:/app/.env \
  -e MODE=cron \
  -e CRON_EXPRESSION="0 2 * * *" \
  -e RUN_IMMEDIATELY=true \
  tc-photo-grabber:latest
```

#### Using Environment Variables

```bash
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -e MODE=cron \
  -e SCHEDULE="every 6 hours" \
  -e TC_EMAIL=your.email@example.com \
  -e TC_PASSWORD=your_password \
  -e SCHOOL=12345 \
  -e CHILD=67890 \
  -e SCHOOL_LAT=41.9032 \
  -e SCHOOL_LNG=-87.6663 \
  -e SCHOOL_KEYWORDS="school, montessori, chicago" \
  tc-photo-grabber:latest

# Or use cron expression instead of SCHEDULE
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -e MODE=cron \
  -e CRON_EXPRESSION="*/30 * * * *" \
  -e TC_EMAIL=your.email@example.com \
  -e TC_PASSWORD=your_password \
  -e SCHOOL=12345 \
  -e CHILD=67890 \
  -e SCHOOL_LAT=41.9032 \
  -e SCHOOL_LNG=-87.6663 \
  -e SCHOOL_KEYWORDS="school, montessori, chicago" \
  tc-photo-grabber:latest
```

## ☸️ Kubernetes Deployment

### Prerequisites

1. Build and push your Docker image:

```bash
docker build -t your-registry/tc-photo-grabber:latest .
docker push your-registry/tc-photo-grabber:latest
```

2. Update the image in `k8s-deployment.yaml`:

```yaml
image: your-registry/tc-photo-grabber:latest
```

### Deploy to Kubernetes

```bash
# Update the secret with your credentials
kubectl create secret generic tc-photo-grabber-secret \
  --from-literal=TC_EMAIL='your.email@example.com' \
  --from-literal=TC_PASSWORD='your_password' \
  --from-literal=SCHOOL='12345' \
  --from-literal=CHILD='67890' \
  --from-literal=SCHOOL_LAT='41.9032' \
  --from-literal=SCHOOL_LNG='-87.6663' \
  --from-literal=SCHOOL_KEYWORDS='school, montessori, chicago'

# Deploy the application
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -l app=tc-photo-grabber
kubectl logs -f deployment/tc-photo-grabber
```

### Customize Schedule

Edit the ConfigMap in `k8s-deployment.yaml`:

```yaml
data:
  SCHEDULE: "every 6 hours"  # or "daily", "hourly", "every day at 10:30"
  # Or use cron expression (takes precedence over SCHEDULE)
  CRON_EXPRESSION: "0 */6 * * *"  # Every 6 hours
```

Then reapply:

```bash
kubectl apply -f k8s-deployment.yaml
kubectl rollout restart deployment/tc-photo-grabber
```

## 📁 Project Structure

```
tc-photo-grabber/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Configuration management
│   ├── client.py            # API client (original auth logic)
│   ├── scheduler.py         # Cron scheduling
│   └── telegram_notifier.py # Telegram notification service
├── Dockerfile               # Docker image definition
├── k8s-deployment.yaml      # Kubernetes manifests
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── TELEGRAM_SETUP.md       # Telegram bot setup guide
└── README.md               # This file
```

## 📱 Telegram Notifications

The application can send notifications to a Telegram channel or chat after each cron job run, including:
- Summary of how many new photos were downloaded
- The new photos themselves (up to 10 photos to avoid spam)

📖 **For detailed setup instructions, see [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)**

### Quick Setup

1. **Create a Telegram Bot:**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the instructions
   - You'll receive a bot token like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

2. **Get Your Chat ID:**
   
   **For a personal chat:**
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response (e.g., `123456789`)
   
   **For a channel:**
   - Add your bot as an administrator to your channel
   - Use the channel username (e.g., `@yourchannel`) or numeric ID (e.g., `-1001234567890`)

3. **Configure the Application:**

   ```bash
   # In .env file
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=@yourchannel
   
   # Or via environment variables
   export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
   export TELEGRAM_CHAT_ID="@yourchannel"
   ```

4. **Test the Connection:**
   
   ```bash
   # Run once to test Telegram notifications
   python -m src
   
   # Run in cron mode with Telegram notifications
   python -m src --cron --cron-expression "0 2 * * *"
   ```

### Telegram Notification Format

After each run, you'll receive:
- ✅ A summary message showing:
  - Number of new photos downloaded
  - Total posts scanned
- 📸 Up to 10 new photos with filenames as captions
- If more than 10 photos were downloaded, a note about remaining photos

Example notification:
```
✅ Photo Sync Complete

📸 New photos downloaded: 5
📋 Total posts scanned: 23

Sending 5 photos...
```

### Docker with Telegram

```bash
docker run -d \
  --name tc-photo-grabber \
  -v $(pwd)/photos:/photos \
  -v $(pwd)/.env:/app/.env \
  -e MODE=cron \
  -e CRON_EXPRESSION="0 2 * * *" \
  -e TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  -e TELEGRAM_CHAT_ID="@yourchannel" \
  tc-photo-grabber:latest
```

### Kubernetes with Telegram

Add to your Secret in `k8s-deployment.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tc-photo-grabber-secret
type: Opaque
stringData:
  tc-email: your.email@example.com
  tc-password: your_password
  telegram-bot-token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  telegram-chat-id: "@yourchannel"
```

Then reference in the Deployment:
```yaml
env:
  - name: TELEGRAM_BOT_TOKEN
    valueFrom:
      secretKeyRef:
        name: tc-photo-grabber-secret
        key: telegram-bot-token
  - name: TELEGRAM_CHAT_ID
    valueFrom:
      secretKeyRef:
        name: tc-photo-grabber-secret
        key: telegram-chat-id
```

## �🔐 Security Notes

- **Never commit credentials** to version control
- Use Kubernetes Secrets for sensitive data in production
- Consider using a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Rotate credentials regularly
- Use read-only file system mounts in containers when possible
- Keep your Telegram bot token secure - treat it like a password

## 📊 Monitoring

### View Logs (Docker)

```bash
docker logs -f tc-photo-grabber
```

### View Logs (Kubernetes)

```bash
kubectl logs -f deployment/tc-photo-grabber
```

### Metrics

The application logs:
- Download start/completion times
- Number of photos discovered
- Number of photos downloaded
- Errors and warnings

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt pytest

# Run tests
pytest tests/
```

### Code Style

```bash
# Format code
black src/

# Lint
pylint src/
```

## 🐛 Troubleshooting

### Login Fails
- Verify credentials in `.env` or config file
- Check if Transparent Classroom website is accessible
- Review logs with `--verbose` flag

### Photos Not Downloading
- Check output directory permissions
- Verify school_id and child_id are correct
- Check cache timeout settings

### Docker Container Exits
- Check logs: `docker logs tc-photo-grabber`
- Verify environment variables are set correctly
- Ensure volumes are properly mounted

### Kubernetes Pod CrashLoopBackOff
- Check secret is created: `kubectl get secret tc-photo-grabber-secret`
- View pod logs: `kubectl logs -f pod-name`
- Verify PVC is bound: `kubectl get pvc`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- Original Rust implementation by [Harper Reed](https://github.com/harperreed)
- Based on the original Python implementation in `get_photos.py`
- Authentication and config logic preserved from original implementation

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs with `--verbose` flag
3. Open an issue on GitHub
