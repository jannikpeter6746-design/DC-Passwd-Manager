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
| Generate a secure password | `/generatepassword [length] [uppercase] [numbers] [symbols]` |
| Full web dashboard | Browse to `http://localhost:5000` |

Passwords are **encrypted at rest** using Fernet symmetric encryption.  
Each entry can be restricted to one or more Discord **roles**.

---

## Quick Start

### Prerequisites

- **Python 3.10 or newer** — check with `python --version`
- **pip** — included with Python; check with `pip --version`
- A **Discord account** with permission to add bots to a server

---

### Step 1 — Create your Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Give it a name (e.g. `DC Passwd Manager`) and confirm.
3. In the left sidebar go to **Bot** and click **Add Bot** → **Yes, do it!**
4. Under the bot's username click **Reset Token**, copy the token and save it — you will need it in Step 4.
5. Still on the **Bot** page, scroll down to **Privileged Gateway Intents** and enable:
   - **Server Members Intent** (needed to resolve role names for the `/addpasswd` command)
6. Click **Save Changes**.

### Step 2 — Invite the bot to your server

1. In the left sidebar go to **OAuth2 → URL Generator**.
2. Under **Scopes** tick: `bot`, `applications.commands`.
3. Under **Bot Permissions** tick: `Manage Channels`, `Manage Guild`.
4. Copy the generated URL at the bottom, paste it in your browser and invite the bot to your server.
5. After the bot joins, **right-click your server name → Copy Server ID** (you need Developer Mode enabled: *User Settings → Advanced → Developer Mode*). Save this ID — it is your `DISCORD_GUILD_ID`.

### Step 3 — Install dependencies

It is recommended to use a virtual environment:

```bash
# create and activate a virtual environment (optional but recommended)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Then install the requirements:

```bash
pip install -r requirements.txt
```

### Step 4 — Configure the environment

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in every value:

| Variable | Where to get it | Example |
|---|---|---|
| `DISCORD_TOKEN` | Step 1 — bot token from the Developer Portal | `MTEx…ABC` |
| `DISCORD_GUILD_ID` | Step 2 — your server ID | `123456789012345678` |
| `ENCRYPTION_KEY` | Generate with the command below | `abc123…=` |
| `DASHBOARD_USERNAME` | Choose a username for the web dashboard | `admin` |
| `DASHBOARD_PASSWORD` | Choose a **strong** password | `s3cr3t!` |
| `FLASK_SECRET_KEY` | Any long random string | `change-me-please-42` |
| `DASHBOARD_PORT` | Port for the web dashboard (default `5000`) | `5000` |

**Generate the encryption key** (run once, paste the output into `.env`):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Step 5 — Start the bot

```bash
python main.py
```

**Expected output:**

```
Dashboard running on port 5000
Logged in as DC Passwd Manager#1234 (ID: 123456789012345678)
```

- The **Discord bot** is now online and slash commands are registered in your guild.  
  Try `/addcategory Google` in any channel.
- The **web dashboard** is available at `http://localhost:5000`  
  (or the port you set in `DASHBOARD_PORT`). Log in with your `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD`.

### Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `RuntimeError: DISCORD_TOKEN is not set` | `.env` is missing or the variable is empty | Copy `.env.example` → `.env` and fill in the token |
| `RuntimeError: ENCRYPTION_KEY is not set` | `ENCRYPTION_KEY` missing from `.env` | Generate a key (Step 4) and add it |
| `RuntimeError: FLASK_SECRET_KEY is not set` | `FLASK_SECRET_KEY` missing from `.env` | Set any long random string in `.env` |
| `discord.errors.LoginFailure: Improper token` | Bot token is wrong or has been reset | Go to Developer Portal → Bot → Reset Token |
| Slash commands don't appear in Discord | Commands take up to 1 hour to propagate globally | Set `DISCORD_GUILD_ID` in `.env` for instant guild sync |
| `Address already in use` on port 5000 | Another process is using the port | Change `DASHBOARD_PORT` in `.env` to e.g. `5001` |

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
- The encryption key lives in `.env` – keep this file secret and **never commit it**.
- Bot commands that show or delete passwords are sent as **ephemeral** messages (only visible to the requester).
- The web dashboard is protected by username/password authentication.
