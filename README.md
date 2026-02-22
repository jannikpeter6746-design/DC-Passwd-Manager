# DC Passwd Manager

A Discord bot + web dashboard for securely managing passwords inside a Discord server.

---

## Features

| Feature | How to use |
|---|---|
| Create password categories | `/addcategory <name>` in Discord |
| Add password entries | `/addpasswd <category> <user/email> <password> [notes] [roles]` |
| List passwords | `/listpasswords <category>` (ephemeral, role-filtered) |
| Delete a password entry | `/deletepassword <id>` |
| Delete a category | `/deletecategory <name>` |
| Full web dashboard | Browse to `http://localhost:5000` |

Passwords are **encrypted at rest** using Fernet symmetric encryption.  
Each entry can be restricted to one or more Discord **roles**.

---

## ▶ Running via GitHub Actions

The easiest way to start the bot **directly from this GitHub repository** – no local machine required.

> ⚠️ **Note:** GitHub Actions jobs run for a maximum of **6 hours** on the free tier.  
> For a permanent, always-on bot see [Deploying permanently](#-deploying-permanently) below.

### Step 1 – Add repository secrets

Go to your repository on GitHub:  
**Settings → Secrets and variables → Actions → New repository secret**

Add each of the following secrets:

| Secret name | Value |
|---|---|
| `DISCORD_TOKEN` | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_GUILD_ID` | Your server/guild ID (Developer Mode → right-click server → Copy ID) |
| `ENCRYPTION_KEY` | Fernet key – see how to generate one below |
| `DASHBOARD_USERNAME` | Username for the web dashboard login |
| `DASHBOARD_PASSWORD` | Password for the web dashboard login |
| `FLASK_SECRET_KEY` | A long random string (e.g. `openssl rand -hex 32`) |

**Generate an encryption key** (run this once locally or in any Python shell):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and save it as the `ENCRYPTION_KEY` secret.

### Step 2 – Trigger the workflow

1. Open the **Actions** tab in your repository.
2. Select **🤖 Run Discord Bot** in the left sidebar.
3. Click **Run workflow** → **Run workflow**.

The bot will start within seconds and stay online for up to 6 hours.  
You can check the live log output directly in the Actions tab.

### Step 3 – Discord bot permissions

In the [Discord Developer Portal](https://discord.com/developers/applications):

- Enable **Server Members Intent** under *Bot → Privileged Gateway Intents*
- Invite the bot with OAuth2 scopes: `bot`, `applications.commands`
- Required bot permissions: **Manage Channels**, **Manage Guild**

---

## 🚀 Deploying permanently

For an always-on bot (beyond the 6-hour Actions limit) deploy to a cheap cloud service:

| Platform | How |
|---|---|
| **Railway** | Connect the repo, set the same environment variables as secrets, set start command `python main.py` |
| **Fly.io** | `fly launch`, add secrets with `fly secrets set DISCORD_TOKEN=…` |
| **Render** | New → Background Worker → connect repo → set env vars → start command `python main.py` |
| **VPS (Ubuntu)** | `git clone`, install deps, create a `.env` file, run with `screen` or `systemd` |

---

## 💻 Local Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and fill in the same variables listed in the secrets table above.

### 3. Run

```bash
python main.py
```

- The Discord bot connects and registers slash commands in your guild.
- The web dashboard is available at `http://localhost:5000`.

---

## Project Structure

```
DC-Passwd-Manager/
├── .github/
│   └── workflows/
│       └── run-bot.yml  # GitHub Actions – manual trigger
├── main.py              # Entry point – starts bot + dashboard
├── bot.py               # Discord bot & slash commands
├── dashboard.py         # Flask web dashboard
├── models.py            # SQLAlchemy database models
├── encryption.py        # Fernet encryption helpers
├── requirements.txt
├── .env.example
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── categories.html
│   ├── passwords.html
│   └── edit_password.html
└── static/
    └── style.css        # Dashboard styles
```

## Screenshots

### Login
![Login page](https://github.com/user-attachments/assets/726834da-c595-4107-97f7-8b54ed1c8071)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/4595beef-3e14-4a9e-8788-4cc63ad5856a)

### Categories
![Categories](https://github.com/user-attachments/assets/cab56cd6-3d97-499d-9daf-4f6e1bf61efb)

### Passwords
![Passwords](https://github.com/user-attachments/assets/9892d7e4-cfcb-4fd0-ad4d-7f6d69fe1b91)

### Edit Password
![Edit Password](https://github.com/user-attachments/assets/6560933e-e721-4793-bd28-ac8be984469d)

---

## Security Notes

- Passwords are encrypted with **Fernet** (AES-128-CBC + HMAC-SHA256) before being stored.
- The encryption key lives in `.env` / GitHub Secrets – **never commit it to the repository**.
- Bot commands that show or delete passwords are sent as **ephemeral** messages (only visible to the requester).
- The web dashboard is protected by username/password authentication.
- Dashboard credentials are compared using constant-time comparison to prevent timing attacks.
