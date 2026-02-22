# DC-Passwd-Manager

A Discord bot that lets you securely save and retrieve passwords via DMs.  
All passwords are encrypted before being stored in memory.

---

## Features

| Command | Description |
|---|---|
| `!addpass <service> <password>` | Save or update a password |
| `!getpass <service>` | Retrieve a saved password |
| `!listpass` | List all saved service names |
| `!deletepass <service>` | Delete a saved password |
| `!help` | Show all commands |

> **Security note:** Use the commands only in a **DM** with the bot so your  
> passwords are never visible in a public channel.

---

## Setup (one-time)

### 1. Create a Discord bot

1. Go to <https://discord.com/developers/applications> and click **New Application**.
2. Open the **Bot** tab → click **Add Bot** → copy the **Token**.
3. Under **Privileged Gateway Intents**, enable **Message Content Intent**.
4. Open **OAuth2 → URL Generator**, select the `bot` scope and the  
   `Send Messages`, `Read Message History`, `Manage Messages` permissions.
5. Open the generated URL, select your server, and click **Authorize**.

### 2. Add GitHub Secrets

In your GitHub repository go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name | Value |
|---|---|
| `DISCORD_TOKEN` | The bot token you copied in step 1 |
| `BOT_SECRET_KEY` | Any long random string (used to encrypt passwords) |

---

## How to start the bot on GitHub

1. Open the **Actions** tab of this repository.
2. Click **Run Discord Bot** in the left sidebar.
3. Click the **Run workflow** button → **Run workflow**.
4. The bot will come online within ~30 seconds and stay connected for up to  
   6 hours (GitHub Actions job limit).

### Keep the bot running continuously

Uncomment the `schedule` block in `.github/workflows/bot.yml` to restart the  
bot automatically every 5 hours 50 minutes:

```yaml
schedule:
  - cron: "50 */5 * * *"
```

---

## Local development

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_TOKEN="your_bot_token"
export BOT_SECRET_KEY="any_long_random_string"

# Run the bot
python bot.py
```

---

## Project structure

```
DC-Passwd-Manager/
├── bot.py                        # Main bot code
├── requirements.txt              # Python dependencies
├── .github/
│   └── workflows/
│       └── bot.yml               # GitHub Actions workflow
└── README.md
```
