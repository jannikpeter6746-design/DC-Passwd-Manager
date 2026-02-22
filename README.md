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

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_GUILD_ID` | Your server/guild ID (Developer Mode → right-click server → Copy ID) |
| `ENCRYPTION_KEY` | Fernet key – generate with the command below |
| `DASHBOARD_USERNAME` | Dashboard login username |
| `DASHBOARD_PASSWORD` | Dashboard login password |
| `FLASK_SECRET_KEY` | Random secret string for Flask sessions |
| `DASHBOARD_PORT` | Port for the web dashboard (default `5000`) |

**Generate an encryption key:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Discord bot permissions

In the Developer Portal enable the following **Privileged Gateway Intents**:
- `SERVER MEMBERS INTENT` (to resolve role names)

Invite the bot with these **OAuth2 scopes**: `bot`, `applications.commands`  
Required bot permissions: `Manage Channels`, `Manage Guild`

### 4. Run

```bash
python main.py
```

- The Discord bot will connect and register slash commands in your guild.
- The web dashboard will be available at `http://localhost:5000` (or the configured port).

---

## Project Structure

```
DC-Passwd-Manager/
├── main.py          # Entry point – starts bot + dashboard
├── bot.py           # Discord bot & slash commands
├── dashboard.py     # Flask web dashboard
├── models.py        # SQLAlchemy database models
├── encryption.py    # Fernet encryption helpers
├── requirements.txt
├── .env.example
├── templates/       # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── categories.html
│   ├── passwords.html
│   └── edit_password.html
└── static/
    └── style.css    # Dashboard styles
```

## Security Notes

- Passwords are encrypted with **Fernet** (AES-128-CBC + HMAC-SHA256) before being stored.
- The encryption key lives in `.env` – keep this file secret and **never commit it**.
- Bot commands that show or delete passwords are sent as **ephemeral** messages (only visible to the requester).
- The web dashboard is protected by username/password authentication.
